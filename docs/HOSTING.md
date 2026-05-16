# Hosting

The correct hosting model depends on whether you want personal automation, a self-hosted web panel, or a public project.

## Recommended: Scheduled Job

Use this when the goal is simply to attempt reservations at specific times.

This repository includes `.github/workflows/weekly-booking.yml`, configured to run every
Saturday at 10:00 in `Europe/Madrid`. Configure `UPV_DNI` and `UPV_PASSWORD` as GitHub
repository secrets, and `UPV_SESSION_CODES` as a repository variable with values such as
`045,060,075`.

Manual workflow runs default to `dry_run=true`, so you can test GitHub Actions without
booking. The scheduled Saturday run always uses real reservation mode.

Good fits:

- GitHub Actions scheduled workflow with repository secrets.
- Render Cron Job.
- Google Cloud Run Job triggered by Cloud Scheduler.
- Fly.io scheduled Machine when approximate hourly/daily/weekly/monthly timing is enough.
- A small VPS with systemd timer or cron.

Pros:

- No public web surface.
- Minimal cost.
- Secrets stay in the platform secret store.

Cons:

- Some free platforms sleep, disable inactive schedules, or have execution limits.
- You need to tune the schedule around the exact reservation opening time.
- GitHub Actions schedules run from the latest commit on the default branch.
- Render cron schedules use UTC.
- Fly.io scheduled Machines are fuzzy interval-based schedules, not exact wall-clock cron.

## Self-Hosted Web Panel

Use Docker or `uvicorn` to run the FastAPI app.

Good fits:

- Render Web Service.
- Fly.io Machine/App.
- Railway service.
- VPS with Docker Compose.

Pros:

- Easy manual dry-runs and protected reservation triggers.
- Health endpoint for monitoring.

Cons:

- Higher security responsibility.
- Must protect `POST /reserve` with `UPV_ADMIN_TOKEN`.
- Still should not collect third-party credentials.

## Public Project

Best public format:

- GitHub repo with clear README, screenshots or architecture diagram, and deploy buttons/templates later.
- Public demo only in dry-run or mocked mode.
- Documentation explaining how each user deploys their own instance.

Avoid:

- A shared hosted site that stores many students' UPV credentials.
- Publishing old notebooks with personal data, cookies, CSV exports, or `chromedriver.exe`.

## Minimal Docker Deployment

```bash
docker build -t upv-gym-booking .
docker run --env-file .env -p 8000:8000 upv-gym-booking
```

## Minimal CLI Deployment

```bash
python -m pip install .
upv-gym-booking --dry-run
upv-gym-booking --reserve
```

## Deployment Examples

- `examples/github-actions-booking.yml`: copy to `.github/workflows/booking.yml` and configure `UPV_DNI` and `UPV_PASSWORD` as repository secrets.
- `examples/render.yaml`: Render cron blueprint. Keep credentials as non-synced environment variables.

## References

- GitHub Actions scheduled workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule
- Render Cron Jobs: https://render.com/docs/cronjobs
- Google Cloud Run jobs on a schedule: https://cloud.google.com/run/docs/execute/jobs-on-schedule
- Fly.io scheduled Machines: https://fly.io/docs/machines/flyctl/fly-machine-run/#start-a-machine-on-a-schedule
