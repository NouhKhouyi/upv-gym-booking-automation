from __future__ import annotations

from dataclasses import replace

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from upv_gym_booking.client import UpvGymClient
from upv_gym_booking.config import BookingConfig, parse_session_codes

app = FastAPI(
    title="UPV Gym Booking Automation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>UPV Gym Booking</title>
        <style>
          :root {
            --ink: #17211d;
            --muted: #607168;
            --paper: #f7f1e6;
            --line: #d9c9af;
            --accent-dark: #8c351f;
            --panel: rgba(255, 252, 245, 0.82);
          }
          * { box-sizing: border-box; }
          body {
            min-height: 100vh;
            margin: 0;
            color: var(--ink);
            font-family: "Aptos", "Segoe UI", sans-serif;
            background:
              radial-gradient(circle at 18% 18%, rgba(216, 95, 52, 0.22), transparent 28rem),
              radial-gradient(circle at 85% 10%, rgba(35, 91, 74, 0.18), transparent 24rem),
              linear-gradient(135deg, #fffaf0 0%, var(--paper) 55%, #e6dcc9 100%);
          }
          main {
            width: min(1040px, calc(100% - 2rem));
            margin: 0 auto;
            padding: 7rem 0 4rem;
          }
          .eyebrow {
            color: var(--accent-dark);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }
          .hero {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 2rem;
            align-items: stretch;
          }
          h1 {
            margin: 0.8rem 0 1rem;
            font-family: Georgia, "Times New Roman", serif;
            font-size: clamp(3rem, 8vw, 6.4rem);
            line-height: 0.88;
            letter-spacing: -0.06em;
          }
          p { color: var(--muted); font-size: 1.05rem; line-height: 1.7; }
          .panel {
            border: 1px solid var(--line);
            border-radius: 2rem;
            background: var(--panel);
            box-shadow: 0 2rem 5rem rgba(74, 57, 33, 0.14);
            backdrop-filter: blur(18px);
            padding: 2rem;
          }
          .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1.8rem;
          }
          a { color: inherit; text-decoration: none; }
          .button {
            display: inline-flex;
            border-radius: 999px;
            padding: 0.85rem 1.1rem;
            font-weight: 800;
            border: 1px solid var(--ink);
          }
          .primary { background: var(--ink); color: #fffaf0; }
          .secondary { background: transparent; }
          .status {
            display: grid;
            gap: 1rem;
            height: 100%;
          }
          .metric {
            border: 1px solid var(--line);
            border-radius: 1.4rem;
            padding: 1.2rem;
            background: rgba(255, 255, 255, 0.42);
          }
          .metric strong {
            display: block;
            font-size: 1.8rem;
            margin-bottom: 0.2rem;
          }
          code {
            background: rgba(23, 33, 29, 0.08);
            padding: 0.15rem 0.35rem;
            border-radius: 0.35rem;
          }
          @media (max-width: 760px) {
            main { padding-top: 3rem; }
            .hero { grid-template-columns: 1fr; }
          }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <div class="panel">
              <div class="eyebrow">Self-hosted automation</div>
              <h1>UPV Gym Booking</h1>
              <p>
                Servicio ligero para listar enlaces candidatos y lanzar reservas desde
                credenciales guardadas en el entorno. Por defecto trabaja en modo seguro:
                sin reserva real hasta pedirlo de forma explicita.
              </p>
              <div class="actions">
                <a class="button primary" href="/dry-run">Ejecutar dry-run</a>
                <a class="button secondary" href="/docs">Ver API</a>
              </div>
            </div>
            <aside class="status">
              <div class="metric">
                <strong>GET /dry-run</strong>
                <span>Comprueba login y parsing sin reservar.</span>
              </div>
              <div class="metric">
                <strong>POST /reserve</strong>
                <span>Requiere <code>X-Admin-Token</code> y secretos de entorno.</span>
              </div>
              <div class="metric">
                <strong>Uso seguro</strong>
                <span>No almacenes credenciales de terceros en una instancia publica.</span>
              </div>
            </aside>
          </section>
        </main>
      </body>
    </html>
    """


@app.get("/dry-run")
def dry_run(codes: str | None = None) -> list[dict[str, str | int | bool | None]]:
    config = _config_for_request(codes=codes, dry_run=True)
    return _run(config)


@app.post("/reserve")
def reserve(
    codes: str | None = None,
    x_admin_token: str | None = Header(default=None),
) -> list[dict[str, str | int | bool | None]]:
    config = _config_for_request(codes=codes, dry_run=False)
    if not config.admin_token:
        raise HTTPException(status_code=403, detail="UPV_ADMIN_TOKEN is not configured.")
    if x_admin_token != config.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token.")
    return _run(config)


def _config_for_request(*, codes: str | None, dry_run: bool) -> BookingConfig:
    config = replace(BookingConfig.from_env(), dry_run=dry_run)
    if codes:
        config = replace(config, session_codes=parse_session_codes(codes))
    return config


def _run(config: BookingConfig) -> list[dict[str, str | int | bool | None]]:
    client = UpvGymClient(config.credentials, timeout_seconds=config.timeout_seconds)
    results = client.run(config)
    return [
        {
            "session_code": f"MUS{result.link.session_code}",
            "label": result.link.label,
            "url": result.link.url,
            "attempted": result.attempted,
            "success": result.success,
            "status_code": result.status_code,
            "message": result.message,
        }
        for result in results
    ]
