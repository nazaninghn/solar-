# SolarFlow Backend

Backend API for SolarFlow Industrial Energy Intelligence Platform.

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- APScheduler (in-process background jobs — no Redis/Celery/separate worker; see "Background jobs" below)

## Development

Create virtual environment:

    python -m venv .venv

Activate environment:

Windows:

    .venv\Scripts\activate

macOS/Linux:

    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Copy `.env.example` to `.env` and fill in real values (never commit `.env`):

    cp .env.example .env

Apply database migrations:

    alembic upgrade head

Run:

    uvicorn app.main:app --reload

Then visit:

- http://localhost:8000 — root status
- http://localhost:8000/health — liveness check
- http://localhost:8000/health/ready — readiness check (includes DB connectivity)
- http://localhost:8000/docs — Swagger UI

## Background jobs

Scheduled jobs (weather/forecast, recommendations, financial calculations,
energy aggregation, alerts, device health, telemetry retention) run
in-process via APScheduler, wired into the FastAPI app's lifespan
(`app/jobs/scheduler.py`). There is no separate worker process and no
Redis — the single web process handles both API requests and scheduled
jobs. Job execution history is tracked in the `job_runs` table and
exposed to platform admins at `GET /api/v1/system/jobs`.

## Deploying to Render

This project needs exactly two Render resources:

1. **PostgreSQL** (managed database) — copy its connection string into `DATABASE_URL`.
   The string Render gives you (`postgres://...` or `postgresql://...`) is
   normalized to this project's driver automatically
   (`app/core/config.py`) — paste it in as-is.
2. **Web Service** (this repo):
   - Build command: `pip install -r requirements.txt`
   - Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     (runs pending migrations before the app starts serving traffic —
     see "Migrations on deploy" below)
   - Health check path: `/health`

No separate Worker or Beat/Scheduler service, and no Redis — those are
only needed for a Celery-based setup, which this project deliberately
doesn't use (see `app/jobs/scheduler.py`'s module docstring).

### Required environment variables

See `.env.example` for the full list. At minimum, set for production:

- `DATABASE_URL` — from the Render Postgres instance
- `JWT_SECRET` — a long random string, not the example placeholder
- `APP_ENV=production`, `DEBUG=false`
- `CORS_ALLOWED_ORIGINS` — your real frontend domain(s), comma-separated, no wildcard

### Migrations on deploy

The start command above runs `alembic upgrade head` before starting
uvicorn, so the process never serves traffic against a schema it
doesn't match. If a migration ever needs to run separately (e.g. a long
migration you want to run once, ahead of a deploy), run it as a Render
one-off job with the same start command's `alembic upgrade head`
portion.
