# Contributing

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,web]"
```

## Checks

```powershell
ruff check .
pytest
```

## Rules

- Do not commit credentials, cookies, generated CSV files, notebooks with outputs, or browser binaries.
- Prefer tests around HTML parsing and configuration behavior.
- Keep real network calls out of the test suite.
- Keep the default mode safe: `dry-run` must remain the default.
