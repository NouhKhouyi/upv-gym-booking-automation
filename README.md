# UPV Gym Booking Automation

Automation toolkit for finding and optionally attempting UPV gym reservation links.

This repository started as two exploratory scripts: one with Selenium and one with direct HTTP requests. The maintained version is now a small Python package with a CLI, an optional FastAPI web service, tests, Docker support, and a safer configuration model based on environment variables.

> Not an official UPV project. Use it only with your own account and only if it complies with the UPV rules for reservations and system usage.

## What It Does

- Logs in to the UPV intranet with credentials provided by environment variables.
- Loads the configured gym activity page.
- Parses reservation links whose labels match target session codes such as `MUS009`.
- Runs in `dry-run` mode by default so you can verify candidates before attempting a real booking.
- Can attempt reservations with retry control when explicitly launched with `--reserve`.
- Exposes an optional self-hosted web service for health checks, dry runs, and protected reservation triggers.

## What Changed From The Legacy Scripts

- No hard-coded local Chrome paths or `chromedriver.exe`.
- No committed `dni.txt`, `contra.txt`, browser cookies, or personal headers.
- No mutation of lists while iterating over reservation links.
- Network behavior is wrapped in a reusable client and covered by parser/config tests.
- The public repo ignores the old local folders and generated CSV/notebook artifacts.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web]"
Copy-Item .env.example .env
```

Edit `.env` with your own credentials. Keep `UPV_DRY_RUN=true` until you have verified the output.

```powershell
upv-gym-booking --dry-run --codes 009,024,039
```

Attempt real reservations only when you are ready:

```powershell
upv-gym-booking --reserve --codes 009,024,039 --attempts 3
```

You can also run the package module directly:

```powershell
python -m upv_gym_booking --dry-run
```

## Configuration

The app loads `.env` automatically if present.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `UPV_DNI` | yes | none | UPV login identifier. |
| `UPV_PASSWORD` | yes | none | UPV password. |
| `UPV_SESSION_CODES` | no | `009,024,039,054,069,010,025,040,055,070` | Target session codes. Both `009` and `MUS009` are accepted. |
| `UPV_DRY_RUN` | no | `true` | Safe mode. If true, no booking request is sent. |
| `UPV_MAX_ATTEMPTS` | no | `3` | Retry attempts for real bookings. |
| `UPV_RETRY_SECONDS` | no | `5` | Delay between retries. |
| `UPV_TIMEOUT_SECONDS` | no | `15` | HTTP timeout. |
| `UPV_ACTIVITY_URL` | no | current gym URL | Override if the UPV endpoint changes. |
| `UPV_ADMIN_TOKEN` | web only | none | Token required by `POST /reserve`. |

## Web Service

Run locally:

```powershell
uvicorn upv_gym_booking.web:app --reload
```

Or with Docker:

```powershell
docker compose up --build
```

Endpoints:

- `GET /health`: liveness check.
- `GET /dry-run?codes=045,060`: logs in, parses candidate links, never books.
- `POST /reserve?codes=045,060`: attempts real reservations and requires `X-Admin-Token: <UPV_ADMIN_TOKEN>`.

Do not run a public service that collects DNI/passwords from other people. The safer open-source model is self-hosted: each user deploys their own instance and stores their own secrets.

## Development

```powershell
ruff check .
pytest
```

CI runs the same checks on Python 3.11 and 3.12.

## Project Layout

```text
src/upv_gym_booking/
  client.py      HTTP login, parsing and reservation flow
  config.py      env/.env configuration
  cli.py         command-line interface
  web.py         optional FastAPI app
tests/           offline tests for parser and config behavior
docs/            architecture, security and hosting notes
```

## Hosting Direction

For personal automation, prefer a scheduled job instead of a public multi-user web app. For a public-looking project, publish this repo, document self-hosting, and optionally provide a small hosted demo that does not accept real credentials.

See [docs/HOSTING.md](docs/HOSTING.md) for concrete deployment options.
