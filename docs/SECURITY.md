# Security Notes

## Secrets

Never commit real credentials. This repo ignores:

- `.env`
- `dni.txt`
- `contra.txt`
- legacy folders with old local experiments

If credentials were ever committed to a public remote, rotate the UPV password and rewrite repository history before publishing.

## Public Access

Do not build a public service where users type their UPV credentials into your server unless you are ready to own the security, legal, operational, and support burden. A safer model is:

- Open-source the code.
- Let each user self-host their own instance.
- Use platform secrets for `UPV_DNI` and `UPV_PASSWORD`.
- Keep any hosted demo in `dry-run` mode and without real credentials.

## Web Endpoint

`POST /reserve` requires `UPV_ADMIN_TOKEN` via `X-Admin-Token`. Use a long random value and store it as a hosting secret.

## Operational Limits

Keep retry counts low. Avoid aggressive polling. Respect UPV reservation rules and avoid load patterns that look abusive.
