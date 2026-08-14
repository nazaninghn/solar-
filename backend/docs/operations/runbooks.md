# SolarFlow — Operations Runbooks

## API Down

1. Check `GET /health` — is it responding?
2. Check Render dashboard — is the service running?
3. Check deploy logs — recent failed deploy?
4. Check application logs for errors
5. Check database connectivity (`/health/ready`)
6. If recent deploy caused it → Rollback
7. If DB issue → check database health
8. Verify recovery: `GET /health` → 200

## Database Down

1. Check Render PostgreSQL dashboard
2. Check connection count (pool exhaustion?)
3. Check recent migrations
4. Check storage (disk full?)
5. If provider issue → wait + monitor
6. If connection pool → restart API service
7. Verify: `GET /health/ready` → ready

## Worker Down

1. Check worker process in Render
2. Check worker logs for crash reason
3. Check queue depth (growing = worker not processing)
4. Check memory/CPU
5. If crash loop → check recent code change
6. Restart worker
7. Verify: queue depth decreasing

## Queue Stuck

1. Check queue size (growing?)
2. Check worker status (alive?)
3. Check failed jobs count
4. Check worker logs for errors
5. Check database (worker can't write?)
6. If safe: restart worker
7. If unsafe: investigate failed jobs first
8. Verify: queue backlog decreasing

## High Latency

1. Identify which endpoints are slow
2. Check database query times
3. Check external API latency
4. Check CPU/memory
5. Check recent deploy (regression?)
6. Look for N+1 queries or missing indexes
7. If external API: check circuit breaker
8. If DB: optimize query or add index

## High Error Rate

1. Check error logs (what's failing?)
2. Check if specific endpoint or widespread
3. Check recent deploy
4. Check database connectivity
5. Check external services
6. If new bug → hotfix or rollback
7. Verify: error rate returns to baseline

## Payment Failure

1. Check payment provider status
2. Check webhook delivery
3. Check credentials (expired?)
4. Check rate limits
5. If provider down → monitor, notify finance team
6. If our bug → fix and retry failed payments

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
