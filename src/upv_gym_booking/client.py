from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from upv_gym_booking.config import DEFAULT_ACTIVITY_URL, BookingConfig, Credentials

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://intranet.upv.es/pls/soalu/"
LOGIN_ACTION_URL = "https://intranet.upv.es/pls/soalu/est_aute.intraalucomp"


class BookingError(RuntimeError):
    """Raised when the booking flow cannot continue safely."""


@dataclass(frozen=True)
class ReservationLink:
    session_code: str
    label: str
    url: str


@dataclass(frozen=True)
class ReservationResult:
    link: ReservationLink
    attempted: bool
    success: bool
    status_code: int | None = None
    message: str = ""


class UpvGymClient:
    def __init__(
        self,
        credentials: Credentials,
        *,
        session: requests.Session | None = None,
        timeout_seconds: float = 15.0,
        user_agent: str = "upv-gym-booking-automation/0.1",
    ) -> None:
        self.credentials = credentials
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9",
            }
        )

    def login(self) -> None:
        response = self.session.post(
            LOGIN_ACTION_URL,
            data={"dni": self.credentials.dni, "clau": self.credentials.password},
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        self._ensure_login_succeeded(response)
        LOGGER.info("Login request completed with HTTP %s", response.status_code)

    def fetch_activity_page(self, activity_url: str = DEFAULT_ACTIVITY_URL) -> str:
        response = self.session.get(
            activity_url,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        self._ensure_activity_page_is_authenticated(response)
        return response.text

    def find_reservation_links(
        self,
        html: str,
        session_codes: tuple[str, ...],
    ) -> list[ReservationLink]:
        return find_reservation_links(html, session_codes)

    def reserve(
        self,
        link: ReservationLink,
        *,
        activity_url: str = DEFAULT_ACTIVITY_URL,
    ) -> ReservationResult:
        action_response = self.session.get(
            link.url,
            timeout=self.timeout_seconds,
            headers={"Referer": activity_url},
        )
        action_response.raise_for_status()

        refresh_response = self.session.get(
            activity_url,
            timeout=self.timeout_seconds,
            headers={"Referer": link.url},
            allow_redirects=True,
        )
        refresh_response.raise_for_status()
        self._ensure_activity_page_is_authenticated(refresh_response)

        success = (
            action_response.status_code == requests.codes.ok
            and refresh_response.status_code == requests.codes.ok
        )
        return ReservationResult(
            link=link,
            attempted=True,
            success=success,
            status_code=refresh_response.status_code,
            message=(
                "Reservation action and refresh completed"
                if success
                else "Reservation flow did not complete"
            ),
        )

    def run(self, config: BookingConfig) -> list[ReservationResult]:
        html, links = self.collect_candidates(config)
        if not links:
            return []

        if config.dry_run:
            return [
                ReservationResult(
                    link=link,
                    attempted=False,
                    success=False,
                    message="Dry run: reservation was not attempted",
                )
                for link in links
            ]

        return self._run_reservations(config, links)

    def collect_candidates(self, config: BookingConfig) -> tuple[str, list[ReservationLink]]:
        self.login()
        html = self.fetch_activity_page(config.activity_url)
        links = self.find_reservation_links(html, config.session_codes)
        LOGGER.info("Found %s candidate reservation links", len(links))
        return html, links

    def _run_reservations(
        self,
        config: BookingConfig,
        links: list[ReservationLink],
    ) -> list[ReservationResult]:
        pending = list(links)
        latest_results: dict[str, ReservationResult] = {}
        for attempt in range(1, config.max_attempts + 1):
            LOGGER.info("Booking attempt %s/%s", attempt, config.max_attempts)
            still_pending: list[ReservationLink] = []

            for link in pending:
                result = self.reserve(link, activity_url=config.activity_url)
                latest_results[link.url] = result
                if result.success:
                    LOGGER.info("Booked candidate %s", link.session_code)
                else:
                    LOGGER.warning(
                        "Booking candidate %s failed with HTTP %s",
                        link.session_code,
                        result.status_code,
                    )
                    still_pending.append(link)

            if not still_pending:
                break

            pending = still_pending
            if attempt < config.max_attempts:
                time.sleep(config.retry_seconds)

        return [latest_results[link.url] for link in links if link.url in latest_results]

    def _ensure_login_succeeded(self, response: requests.Response) -> None:
        url_upper = response.url.upper()
        body_upper = response.text.upper()
        if "EST_AUTE.VERERROR" in url_upper or "P_CODERROR=" in url_upper:
            raise BookingError(f"UPV login failed. Error page: {response.url}")
        if "ERR15" in body_upper:
            raise BookingError(
                "UPV login failed with ERR15 (check DNI/password or login constraints)."
            )
        if "NAME=\"DNI\"" in body_upper and "NAME=\"CLAU\"" in body_upper:
            raise BookingError(
                "UPV login failed: returned to login form instead of an authenticated page."
            )

    def _ensure_activity_page_is_authenticated(self, response: requests.Response) -> None:
        body_upper = response.text.upper()
        if "EST_AUTE.VERERROR" in response.url.upper() or "P_CODERROR=" in response.url.upper():
            raise BookingError(f"UPV activity page returned an error page: {response.url}")
        if "NAME=\"DNI\"" in body_upper and "NAME=\"CLAU\"" in body_upper:
            raise BookingError("UPV session is not authenticated when opening the activity page.")


def find_reservation_links(
    html: str,
    session_codes: tuple[str, ...],
) -> list[ReservationLink]:
    soup = BeautifulSoup(html, "html.parser")
    wanted_codes = tuple(code.upper().removeprefix("MUS").zfill(3) for code in session_codes)

    found_by_code: dict[str, ReservationLink] = {}
    for row in soup.find_all("tr"):
        for cell in row.find_all(["td", "th"]):
            cell_text = cell.get_text(separator=" ", strip=True)
            cell_links = cell.find_all("a")
            for code in wanted_codes:
                if code in found_by_code or not _matches_code(cell_text, "", code):
                    continue
                reservation_anchor = next(
                    (anchor for anchor in cell_links if _is_reservation_href(anchor.get("href"))),
                    None,
                )
                if reservation_anchor is None:
                    continue
                found_by_code[code] = _reservation_link_from_anchor(
                    reservation_anchor,
                    session_code=code,
                    fallback_label=cell_text,
                )

        row_text = row.get_text(separator=" ", strip=True)
        reservation_anchors = [
            anchor for anchor in row.find_all("a") if _is_reservation_href(anchor.get("href"))
        ]
        if len(reservation_anchors) != 1:
            continue
        for code in wanted_codes:
            if code in found_by_code or not _matches_code(row_text, "", code):
                continue
            found_by_code[code] = _reservation_link_from_anchor(
                reservation_anchors[0],
                session_code=code,
                fallback_label=row_text,
            )

    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        label = anchor.get_text(separator=" ", strip=True)
        if not href or _is_cancel_href(href):
            continue
        classes = anchor.get("class", [])
        is_old_selector = "upv_enlacelista" in classes
        is_new_selector = _is_reservation_href(href)
        if not is_old_selector and not is_new_selector:
            continue

        for code in wanted_codes:
            if code in found_by_code:
                continue
            if not _matches_code(label, href, code):
                continue
            found_by_code[code] = _reservation_link_from_anchor(
                anchor,
                session_code=code,
                fallback_label=label,
            )

    return [found_by_code[code] for code in wanted_codes if code in found_by_code]


def _reservation_link_from_anchor(
    anchor,
    *,
    session_code: str,
    fallback_label: str,
) -> ReservationLink:
    href = anchor.get("href", "")
    label = anchor.get_text(separator=" ", strip=True) or fallback_label
    return ReservationLink(
        session_code=session_code,
        label=label,
        url=urljoin(BASE_URL, href),
    )


def _is_reservation_href(href: str | None) -> bool:
    if not href:
        return False
    href_upper = href.upper()
    return "HSEMACTMATRI" in href_upper or (
        "HSEMACTDESMAT" not in href_upper and "RESERVA" in href_upper
    )


def _is_cancel_href(href: str) -> bool:
    return "HSEMACTDESMAT" in href.upper()


def _matches_code(label: str, href: str, code: str) -> bool:
    label_upper = (label or "").upper()
    href_upper = href.upper()
    if f"MUS{code}" in label_upper or f"MUS{code}" in href_upper:
        return True
    return re.search(rf"(?<!\d){re.escape(code)}(?!\d)", label_upper) is not None
