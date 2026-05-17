# UPV Gym Booking Automation

Self-hosted automation for UPV gym reservations. It logs in with your own UPV account, reads the current gym activity table, finds the sessions you want, and reserves them either from the CLI, from a small FastAPI service, or automatically with GitHub Actions.

> Unofficial project. Use it only with your own account and respect UPV reservation rules.

## Current Setup

- Maintained implementation: Python package in `src/upv_gym_booking`.
- Main backend: `requests` + `BeautifulSoup`, no browser driver required.
- Default activity endpoint: current `sic_depact.HSemActividades` gym page.
- Reservation flow: `HSemActMatri` action, then activity-page refresh and confirmation check.
- Weekly automation: `.github/workflows/weekly-booking.yml`.
- Default schedule: every Saturday at `10:00 Europe/Madrid`.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web]"
Copy-Item .env.example .env
```

Edit `.env` with your own credentials.

Test without booking:

```powershell
upv-gym-booking --dry-run --codes 045 --debug-dir debug\test045 -v
```

Reserve one session:

```powershell
upv-gym-booking --reserve --codes 045 --attempts 1 --debug-dir debug\reserve045 -v
```

## GitHub Actions Automation

Configure the repository in GitHub:

Secrets:

```text
UPV_DNI
UPV_PASSWORD
```

Variables:

```text
UPV_SESSION_CODES=045,060,075
```

Optional variable if UPV changes the activity URL:

```text
UPV_ACTIVITY_URL=https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?...
```

The scheduled workflow runs every Saturday at `10:00 Europe/Madrid` and uses real reservation mode. Manual workflow runs also default to real reservation mode; set `dry_run=true` only when you want a test run.

Manual test path:

```text
Actions > Weekly UPV booking > Run workflow
```

Use:

```text
codes: 045
dry_run: false
```

Every run uploads a `booking-debug` artifact with the detected links and, for real reservations, the action and refresh HTML used to confirm the booking.

## Configuration

The app loads `.env` automatically if present.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `UPV_DNI` | yes | none | UPV login identifier. |
| `UPV_PASSWORD` | yes | none | UPV password. |
| `UPV_SESSION_CODES` | no | `009,024,039,054,069,010,025,040,055,070` | Target session codes. Both `045` and `MUS045` are accepted. |
| `UPV_ACTIVITY_URL` | no | packaged current gym URL | Activity listing page. Override when UPV changes endpoints. |
| `UPV_DRY_RUN` | no | `true` | Safe local default. |
| `UPV_MAX_ATTEMPTS` | no | `3` | Retry attempts for real bookings. |
| `UPV_RETRY_SECONDS` | no | `5` | Delay between retries. |
| `UPV_TIMEOUT_SECONDS` | no | `15` | HTTP timeout. |
| `UPV_ADMIN_TOKEN` | web only | none | Token required by `POST /reserve`. |

## Web Service

Run locally:

```powershell
uvicorn upv_gym_booking.web:app --reload
```

Endpoints:

- `GET /health`
- `GET /dry-run?codes=045,060`
- `POST /reserve?codes=045,060` with `X-Admin-Token`

Docker:

```powershell
docker compose up --build
```

Do not run a public shared service that collects other students' UPV credentials. The intended public model is open-source and self-hosted.

## Development

```powershell
ruff check .
pytest
```

CI runs lint and tests on Python 3.11 and 3.12.

## Project Layout

```text
src/upv_gym_booking/
  client.py      Login, parsing, reservation and confirmation flow
  config.py      Environment and .env configuration
  cli.py         Command-line interface and debug artifacts
  web.py         Optional FastAPI app
tests/           Offline tests for parser, config and confirmation behavior
docs/            Architecture, hosting and security notes
```

## Security

Never commit `.env`, `dni.txt`, `contra.txt`, debug artifacts, cookies, notebooks with outputs, or browser profiles. This repo ignores those by default. If real credentials were ever pushed to a public remote, rotate the UPV password.

## Legacy Cleanup

The original Selenium scripts and exploratory notebooks were removed from `main` because they depended on local machine paths, browser binaries, cookies and ad hoc credential files. The maintained code path is the package in `src/`.
