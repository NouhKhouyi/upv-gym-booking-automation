# Architecture

## Main Flow

1. `BookingConfig.from_env()` loads `.env` and environment variables.
2. `UpvGymClient.login()` posts credentials to the UPV login endpoint.
3. `UpvGymClient.fetch_activity_page()` downloads the configured activity page.
4. `find_reservation_links()` extracts anchors with class `upv_enlacelista` and filters labels matching the configured `MUSxxx` codes.
5. In `dry-run`, the app returns the candidate links without booking.
6. In real mode, the client attempts each reservation link and retries failed candidates.

## Design Choices

- Requests-based implementation is the maintained path because it is cheaper to run, easier to host, and avoids browser-driver drift.
- Selenium is intentionally not part of the maintained package. It is useful for exploration when the site changes, but it is a poor production dependency for a scheduled reservation bot.
- Credentials are provided through environment variables, never through committed text files.
- The web app is intentionally admin-only and self-hosted. It is not designed to be a central multi-user credential vault.

## Extension Points

- Add richer response parsing in `UpvGymClient.reserve()` if the UPV page exposes reliable success/error text.
- Add a scheduler process if you need in-process timing. For hosting, an external scheduler or cron job is usually more reliable.
- Add notification hooks after a run, for example email, Telegram, Discord, or Slack.
