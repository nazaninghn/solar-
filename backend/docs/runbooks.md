# SolarFlow Backend — Runbooks

Quick reference for common production failure scenarios. Written for
this project's actual architecture: one Render Web Service running
FastAPI + an in-process APScheduler (no Redis, no Celery, no separate
worker — see `app/jobs/scheduler.py`'s module docstring for why).

Tools referenced throughout:
- `GET /health` — pure liveness (process is up)
- `GET /health/ready` — DB connectivity
- `GET /api/v1/system/health` — full operator view (API/DB/scheduler/devices/external APIs), SUPER_ADMIN only
- `GET /api/v1/system/jobs` — latest run of every scheduled job, SUPER_ADMIN only
- `GET /api/v1/system/metrics` — request/device/DB-pool/external-API counters, SUPER_ADMIN only

---

## Database down / unreachable

**Symptoms:** `/health/ready` returns `{"status": "not_ready", "database": "error"}`.
Most API requests fail. `/api/v1/system/health` shows `"database": {"status": "unhealthy"}`.

1. Check `/health/ready` to confirm it's genuinely the DB, not something else.
2. Check the Render Postgres instance's own status page/dashboard — is it running, or is it a Render-side outage?
3. Check `DATABASE_URL` is still correct (did the Postgres instance get recreated, rotating the connection string?).
4. Check connection pool exhaustion via `GET /api/v1/system/metrics` → `database.checked_out` vs `database.pool_size` — if checked_out is pegged at pool_size, something is holding connections open (a long-running query, a leaked session) rather than the DB itself being down.
5. If the DB process itself is down, this is a Render-side incident — nothing to fix in this codebase; wait for Render's Postgres to recover, then confirm `/health/ready` goes back to `ready`.
6. Once recovered, check `GET /api/v1/system/jobs` for any jobs that failed with a DB-related error during the outage — the next scheduled run will retry automatically, no manual re-run needed for anything using the idempotent upsert pattern (aggregation, forecasts, financial records).

## Weather API down (Open-Meteo)

**Symptoms:** `/api/v1/system/health` → `external_apis.providers.weather.status` is `"degraded"` or `"unhealthy"`. Solar forecast job (`generate_solar_forecasts`, `GET /api/v1/system/jobs`) shows recent failures. Forecast API responses have `is_stale: true`.

1. Check `GET /api/v1/system/metrics` → `external_apis.weather` for the actual success rate and recent failure/timeout counts.
2. The circuit breaker (`app/core/circuit_breaker.py`, wired into `app/weather/providers/open_meteo_provider.py`) opens automatically after 5 consecutive failures and stops sending requests for 60 seconds at a time — if it's OPEN, no action needed, it will self-test recovery automatically. This is not something to "fix" manually.
3. Confirm the fallback is working: `GET /api/v1/factories/{id}/forecast/solar` should still return the last successfully-stored forecast with `is_stale: true`, not an empty response — if the dashboard is blank instead of showing stale data, that's a real bug, not expected degraded-mode behavior.
4. If Open-Meteo is down for an extended period (check https://open-meteo.com status externally), there's nothing to do but wait — no API key/quota to check, since Open-Meteo requires none by default (`WEATHER_API_KEY` is unused unless a different provider is configured via `WEATHER_BASE_URL`).
5. If `WEATHER_BASE_URL` was changed to a different provider that DOES need a key, verify `WEATHER_API_KEY` is set and not expired.

## Scheduler / background jobs not running

**Symptoms:** `/api/v1/system/health` → `scheduler.status` is `"unhealthy"` (APScheduler itself isn't running) or `"degraded"` (it's running, but the latest run of one or more jobs failed). Dashboard data goes stale — forecasts, financial records, aggregations stop updating.

1. `scheduler.status: "unhealthy"` means the APScheduler instance inside the FastAPI process isn't running at all — this only happens if `start_scheduler()` (`app/main.py`'s lifespan) never ran or the process is in a bad state. Restart the Render Web Service.
2. `scheduler.status: "degraded"` means the scheduler is fine but a specific job is failing — check `GET /api/v1/system/jobs`, find the job with `status: "failed"`, read its `error_message`.
3. Since there's no separate worker to restart (jobs run in-process), a job failure doesn't need a service restart — the next scheduled run will simply retry. If a job needs to run immediately rather than waiting for its next scheduled time, it can be invoked directly via a one-off script (see any `app/jobs/*.py` module — each exposes a plain function you can call).
4. If jobs are failing because of a downstream dependency (DB, weather API), fix that first — see the relevant runbook above.

## Device offline

**Symptoms:** `/api/v1/system/health` → `devices.offline > 0`. A `SYSTEM` notification fires automatically ("System health issue detected") once `device_health_jobs.check_device_health` (runs every 5 minutes) marks the device `OFFLINE` after 15 minutes of no telemetry.

1. Check the device's `last_seen_at` via `GET /api/v1/devices/{id}` — how long has it actually been silent?
2. If it's a `SIMULATOR` device (dev/test only), check `GET /api/v1/system/simulator-scenario` — someone may have switched to the `DEVICE_OFFLINE` scenario deliberately.
3. For a real device (once real hardware/API/MQTT/Modbus adapters exist — currently only SIMULATOR is implemented, see `app/devices/modbus.py`/`mqtt.py`/`api.py`'s stub docstrings), check the device's own connectivity, power, and network path.
4. Once the device resumes sending telemetry (via `POST /api/v1/devices/{id}/telemetry` or the polling loop), its status flips back to `ONLINE` automatically on the next successful read — no manual reset needed.
5. The alert auto-resolves: once `_get_offline_devices` no longer includes this device, the next alert-engine cycle (every 5 minutes, `app/jobs/alert_jobs.py`) automatically transitions the existing notification to `RESOLVED` and posts a recovery notice (`app/modules/notifications/engine.py:_auto_resolve_if_active`).

## High error rate

**Symptoms:** `/api/v1/system/health` → `api.status: "unhealthy"` (error rate over 5%). `GET /api/v1/system/metrics` → `requests.error_rate_percent` confirms the number; `requests.bucket_counts` shows how many requests are landing in the "slow" bucket.

1. Check application logs (structured JSON if `LOG_FORMAT=json`) for the specific failing requests — every request is logged with a `request_id`, `status`, `duration_ms`, and (for authenticated requests) `user_id`/`organization_id`. If a user reports an error, ask for the `X-Request-ID` response header value and grep logs for it directly.
2. If errors cluster around one endpoint, check whether it's a code bug (deploy a fix) or a downstream dependency failure (DB/weather — see above).
3. If `SENTRY_DSN` is configured, check the Sentry project for full stack traces — otherwise, the structured logs' `error` field (populated via `logger.exception`) has the traceback.
4. If the error rate spike correlates with a recent deploy, consider rolling back on Render while investigating.
