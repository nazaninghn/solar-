# SolarFlow — Operations Runbooks

**87: `docs/runbooks.md` (repo root) is the current, actively-maintained
runbook set — written with this project's real architecture (single
Render instance, in-process APScheduler, no separate worker) and exact
endpoint references (`/api/v1/system/health`, `/api/v1/system/jobs`,
`/api/v1/system/metrics`). For API Down, Database Down, High Latency, and
High Error Rate, start there — it has real endpoint paths and response
fields to check, not just generic steps.**

This file's **Worker Down** and **Queue Stuck** sections below are N/A —
there is no separate worker process (`docs/architecture-decisions.md`'s
ADR-1: APScheduler runs in-process, confirmed no separate worker exists
anywhere in this codebase). **Payment Failure** is also N/A — no payment
gateway integration exists (confirmed by grep, `docs/policies/
vendor-policy.md`). Kept here for historical reference, not because
they're live procedures. **Storage Full** and **Security Incident** below
remain real and aren't duplicated in `docs/runbooks.md`.

## API Down — see `docs/runbooks.md` instead

## Database Down — see `docs/runbooks.md`'s "Database down / unreachable"

## Worker Down — N/A, no separate worker exists (see note above)

## Queue Stuck — N/A, no separate queue exists (see note above)

## High Latency — see `docs/operations/performance-scalability-report.md` for the real, measured bottleneck (connection pool) and its fix

## High Error Rate — see `docs/runbooks.md`'s "High error rate"

## Payment Failure — N/A, no payment gateway integration exists (see note above)

## Storage Full

1. Check database size
2. Check telemetry table growth
3. Check log volume
4. Apply retention policy (archive/delete old data)
5. If urgent: increase storage allocation
6. Plan long-term: partitioning, archival

## Security Incident

1. **CONTAIN** — Block suspicious access
2. Revoke compromised credentials
3. Rotate secrets
4. Check audit logs for scope of breach
5. Preserve evidence (don't delete logs)
6. Deploy rotated secrets
7. Investigate root cause
8. Notify stakeholders
9. Post-incident review
