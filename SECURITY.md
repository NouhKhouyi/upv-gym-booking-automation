# Security Policy

This project automates actions against a university intranet account. Treat credentials as high-risk secrets.

## Supported Use

- Self-host with your own UPV account.
- Store secrets in `.env` locally or in your hosting provider's secret store.
- Keep `UPV_DRY_RUN=true` until you have verified the parsed reservation links.

## Unsupported Use

- Do not run a shared public instance that collects credentials from other students.
- Do not commit `dni.txt`, `contra.txt`, `.env`, cookies, browser profiles, or old notebooks with private outputs.
- Do not use aggressive polling or retries.

## Reporting Issues

If this repository is public and you find a security issue, open a private advisory on GitHub if available. Otherwise contact the maintainer directly and avoid posting credentials or live session data in issues.
