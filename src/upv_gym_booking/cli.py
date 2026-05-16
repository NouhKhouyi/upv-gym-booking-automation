from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import replace
from pathlib import Path

from bs4 import BeautifulSoup

from upv_gym_booking.client import UpvGymClient
from upv_gym_booking.config import BookingConfig, parse_session_codes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upv-gym-booking",
        description="Find and optionally attempt UPV gym reservations.",
    )
    parser.add_argument("--codes", help="Comma-separated session codes, e.g. 009,024,MUS039")
    parser.add_argument("--attempts", type=int, help="Maximum booking attempts")
    parser.add_argument("--retry-seconds", type=float, help="Seconds between retry attempts")
    parser.add_argument("--timeout-seconds", type=float, help="HTTP timeout in seconds")
    parser.add_argument("--activity-url", help="Override the UPV activity page URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list matching reservation links",
    )
    parser.add_argument(
        "--debug-dir",
        help="Directory to store fetched HTML and link diagnostics",
    )
    parser.add_argument("--reserve", action="store_true", help="Attempt real reservations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.dry_run and args.reserve:
        print("Choose either --dry-run or --reserve, not both.", file=sys.stderr)
        return 2

    try:
        config = BookingConfig.from_env()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    overrides = {}
    if args.codes:
        overrides["session_codes"] = parse_session_codes(args.codes)
    if args.attempts is not None:
        overrides["max_attempts"] = args.attempts
    if args.retry_seconds is not None:
        overrides["retry_seconds"] = args.retry_seconds
    if args.timeout_seconds is not None:
        overrides["timeout_seconds"] = args.timeout_seconds
    if args.activity_url:
        overrides["activity_url"] = args.activity_url
    if args.dry_run:
        overrides["dry_run"] = True
    if args.reserve:
        overrides["dry_run"] = False

    config = replace(config, **overrides)
    client = UpvGymClient(config.credentials, timeout_seconds=config.timeout_seconds)

    try:
        if args.debug_dir:
            html, links = client.collect_candidates(config)
            _write_debug_artifacts(
                output_dir=Path(args.debug_dir),
                activity_url=config.activity_url,
                html=html,
                target_codes=config.session_codes,
                matched_links=links,
            )
            if config.dry_run:
                results = [
                    {
                        "session_code": link.session_code,
                        "label": link.label,
                        "url": link.url,
                    }
                    for link in links
                ]
                if not results:
                    print("No matching reservation links found.")
                    return 0
                for item in results:
                    print(f"[DRY-RUN] MUS{item['session_code']} | {item['label']} | {item['url']}")
                return 0
            debug_dir = Path(args.debug_dir)
            results = client._run_reservations(config, links, debug_dir=debug_dir)
            _write_results_artifact(debug_dir, results)
        else:
            results = client.run(config)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Booking flow failed")
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No matching reservation links found.")
        return 0

    for result in results:
        status = "DRY-RUN" if not result.attempted else ("OK" if result.success else "FAIL")
        suffix = f" HTTP {result.status_code}" if result.status_code is not None else ""
        print(
            f"[{status}] MUS{result.link.session_code} | "
            f"{result.link.label} | {result.link.url}{suffix}"
        )
        if result.attempted:
            print(f"  action_url: {result.action_url}")
            print(f"  refresh_url: {result.refresh_url}")
            print(f"  message: {result.message}")

    failed_attempts = [result for result in results if result.attempted and not result.success]
    return 1 if failed_attempts else 0


def _write_debug_artifacts(
    *,
    output_dir: Path,
    activity_url: str,
    html: str,
    target_codes: tuple[str, ...],
    matched_links: list,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "activity_page.html").write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")
    anchor_preview = []
    for anchor in anchors[:120]:
        label = anchor.get_text(separator=" ", strip=True)
        href = anchor.get("href")
        if not label and not href:
            continue
        anchor_preview.append({"label": label[:180], "href": href})

    summary = {
        "activity_url": activity_url,
        "target_codes": list(target_codes),
        "matched_count": len(matched_links),
        "matched_links": [
            {"session_code": link.session_code, "label": link.label, "url": link.url}
            for link in matched_links
        ],
        "anchor_count_total": len(anchors),
        "anchor_preview_first_120": anchor_preview,
        "activity_rows": _summarize_activity_rows(soup),
    }
    (output_dir / "debug_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"Debug artifacts written to: {output_dir}")


def _write_results_artifact(output_dir: Path, results: list) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "session_code": f"MUS{result.link.session_code}",
            "label": result.link.label,
            "reservation_url": result.link.url,
            "attempted": result.attempted,
            "success": result.success,
            "status_code": result.status_code,
            "message": result.message,
            "action_url": result.action_url,
            "refresh_url": result.refresh_url,
        }
        for result in results
    ]
    (output_dir / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _summarize_activity_rows(soup: BeautifulSoup) -> list[dict[str, str | None]]:
    rows = []
    for row in soup.find_all("tr"):
        row_text = row.get_text(separator=" ", strip=True)
        links = row.find_all("a")
        reservation_href = _first_href_containing(links, "HSEMACTMATRI")
        cancel_href = _first_href_containing(links, "HSEMACTDESMAT")
        if "MUS" not in row_text.upper() and reservation_href is None and cancel_href is None:
            continue
        rows.append(
            {
                "row_text": row_text[:260],
                "reservation_href": reservation_href,
                "cancel_href": cancel_href,
            }
        )
    return rows


def _first_href_containing(links, needle: str) -> str | None:
    for link in links:
        href = link.get("href")
        if href and needle in href.upper():
            return href
    return None
