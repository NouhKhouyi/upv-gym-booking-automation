from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ACTIVITY_URL = (
    "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades"
    "?p_campus=V&p_codacti=21809&p_vista=intranet&p_idioma=i&p_tipoact=6846"
    "&p_solo_matricula_sn=&p_anc=bloque_inscritas"
)

DEFAULT_SESSION_CODES = ("009", "024", "039", "054", "069", "010", "025", "040", "055", "070")


@dataclass(frozen=True)
class Credentials:
    dni: str
    password: str


@dataclass(frozen=True)
class BookingConfig:
    credentials: Credentials
    session_codes: tuple[str, ...] = DEFAULT_SESSION_CODES
    activity_url: str = DEFAULT_ACTIVITY_URL
    dry_run: bool = True
    max_attempts: int = 3
    retry_seconds: float = 5.0
    timeout_seconds: float = 15.0
    admin_token: str | None = None

    @classmethod
    def from_env(cls, *, env_file: str | Path | None = ".env") -> BookingConfig:
        if env_file is not None:
            load_env_file(Path(env_file))

        dni = os.getenv("UPV_DNI", "").strip()
        password = os.getenv("UPV_PASSWORD", "")
        if not dni or not password:
            raise ValueError("Missing UPV_DNI or UPV_PASSWORD. Configure them in .env or env vars.")

        return cls(
            credentials=Credentials(dni=dni, password=password),
            session_codes=parse_session_codes(
                os.getenv("UPV_SESSION_CODES", ",".join(DEFAULT_SESSION_CODES))
            ),
            activity_url=os.getenv("UPV_ACTIVITY_URL", DEFAULT_ACTIVITY_URL).strip(),
            dry_run=parse_bool(os.getenv("UPV_DRY_RUN"), default=True),
            max_attempts=parse_int(os.getenv("UPV_MAX_ATTEMPTS"), default=3),
            retry_seconds=parse_float(os.getenv("UPV_RETRY_SECONDS"), default=5.0),
            timeout_seconds=parse_float(os.getenv("UPV_TIMEOUT_SECONDS"), default=15.0),
            admin_token=os.getenv("UPV_ADMIN_TOKEN") or None,
        )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_session_codes(raw_value: str) -> tuple[str, ...]:
    codes: list[str] = []
    for item in raw_value.replace(";", ",").split(","):
        code = item.strip().upper()
        if not code:
            continue
        if code.startswith("MUS"):
            code = code[3:]
        codes.append(code.zfill(3))
    return tuple(dict.fromkeys(codes))


def parse_bool(raw_value: str | None, *, default: bool) -> bool:
    if raw_value is None or raw_value == "":
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int(raw_value: str | None, *, default: int) -> int:
    if raw_value is None or raw_value == "":
        return default
    return int(raw_value)


def parse_float(raw_value: str | None, *, default: float) -> float:
    if raw_value is None or raw_value == "":
        return default
    return float(raw_value)
