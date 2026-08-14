# SolarFlow — Observability Overview (STEP 63)

## Three Pillars

| Pillar | Purpose | Implementation |
|--------|---------|----------------|
| **Logs** | What happened | Structured JSON, request_id, correlation_id |
| **Metrics** | How much/fast | API latency, error rate, queue depth |
| **Traces** | Where it went | Request path through services |

## Golden Signals

| Signal | What to Watch | Alert Threshold |
|--------|---------------|-----------------|
| Latency | P95 response time | > 2x baseline |
| Traffic | Requests/min | Sudden spike/drop |
| Errors | 5xx rate | > 2% |
| Saturation | CPU, Memory, DB connections | > 80% |

## SLIs & SLOs

| Service | SLI | SLO Target |
|---------|-----|------------|
| API Availability | Successful requests / Total | ≥ 99.5% |
| API Latency | P95 response time | ≤ 500ms |
| Telemetry Ingest | Successful ingestion rate | ≥ 99% |
| Queue Processing | Jobs completed / Jobs created | ≥ 99% |
| Data Freshness | Age of latest telemetry | ≤ 5 min |

## Dashboards

### 1. System Health (`/admin/monitoring/overview`)
- API status, DB, Queue, Workers
- Error rate, latency, traffic

### 2. Factory Health (`/factories/{id}/observability/health`)
- Device availability, data quality, freshness
- Energy balance validation

### 3. Security (`/admin/security/events/summary`)
- Failed logins, lockouts, suspicious activity

### 4. Business
- Active orgs, devices online, telemetry volume
- Recommendations generated, savings realized

## Alert Design Principles

1. **Actionable** — Every alert should have a clear next step
2. **Not noisy** — Only alert on real problems
3. **Severity-based** — CRITICAL = act now, WARNING = investigate soon
4. **Linked to runbook** — Each alert points to resolution steps
5. **Deduplicated** — One incident = one alert, not 100

## Structured Log Format

```json
{
  "timestamp": "2026-08-14T12:30:00Z",
  "level": "ERROR",
  "service": "api",
  "request_id": "req_abc123",
  "user_id": 42,
  "organization_id": 7,
  "endpoint": "/api/v1/devices",
  "error_code": "DB_TIMEOUT",
  "duration_ms": 5200
}
```

## Never Log
- Passwords
- Access/Refresh tokens
- API secrets
- Credit card data
- Private keys

## Monitoring Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness (process alive) |
| `GET /health/ready` | Readiness (DB connected) |
| `GET /api/v1/system/health/full` | All dependencies |
| `GET /api/v1/admin/monitoring/overview` | Platform dashboard |
| `GET /api/v1/admin/security/events/summary` | Security 24h |

## Data Freshness Monitoring

For each factory, track:
- Last telemetry received per device
- If gap > threshold → STALE alert
- If gap > 2x threshold → OFFLINE alert

## Synthetic Monitoring

Periodically test critical paths:
1. `GET /health` (every 1 min)
2. Login flow (every 5 min)
3. Critical API endpoint (every 5 min)

## Incident Response Flow

```
Alert → Acknowledge → Investigate → Mitigate → Resolve → Postmortem
```

See: `docs/operations/incidents.md` for full process.
See: `docs/operations/runbooks.md` for specific scenarios.
