# SolarFlow — Disaster Recovery Plan (STEP 59)

## Recovery Objectives

| Service | RPO | RTO | Priority |
|---------|-----|-----|----------|
| API | 15 min | 30 min | Critical |
| Database | 1 hour | 1 hour | Critical |
| Telemetry | 1 hour | 2 hours | High |
| Billing | 15 min | 1 hour | Critical |
| Analytics | 4 hours | 4 hours | Medium |
| Reports | 24 hours | 8 hours | Low |

## Disaster Scenarios

### 1. Database Failure
**Detect:** `/health/ready` fails, 500 errors spike
**Recover:**
1. Check Render PostgreSQL dashboard
2. If provider issue → wait for provider recovery
3. If data corruption → restore from backup
4. Verify schema + data integrity
5. Reconnect backend
6. Smoke test

### 2. Bad Deployment
**Detect:** Error rate spikes after deploy
**Recover:**
1. Confirm deploy caused it (timing correlation)
2. Rollback to previous deploy in Render
3. Verify health checks pass
4. Investigate root cause in staging

### 3. Accidental Data Deletion
**Detect:** User report or monitoring anomaly
**Recover:**
1. STOP — don't overwrite more data
2. Identify scope (what was deleted)
3. Select backup closest to deletion time
4. Restore to recovery environment
5. Extract deleted records
6. Apply to production
7. Verify

### 4. Credential Compromise
**Detect:** Unauthorized access in audit logs, alerts
**Recover:**
1. CONTAIN — revoke compromised credentials immediately
2. Rotate ALL affected secrets
3. Deploy with new secrets
4. Review audit logs for damage scope
5. Notify affected parties
6. Post-incident security review

### 5. Complete Production Outage
**Recover:**
1. New Render Web Service (or fix existing)
2. Verify/restore database
3. Set environment variables
4. Deploy from known-good commit
5. Run migrations
6. Verify health
7. Connect frontend
8. Full smoke test

## Backup Policy

### What's Backed Up
- PostgreSQL database (managed by Render)
- Application configuration (.env.example as template)
- Source code (GitHub)

### Render PostgreSQL Backups
- Automatic daily backups
- Point-in-time recovery available (plan dependent)
- Stored in Render's infrastructure

### Our Responsibilities
- Verify backup existence regularly
- Test restore periodically
- Document restore procedure
- Keep secrets in secure location (not Git)

## Recovery Runbook

```
1. DETECT    — Alert fires or user reports
2. ASSESS    — What failed? What's the scope?
3. CONTAIN   — Stop further damage
4. PLAN      — Choose recovery strategy
5. EXECUTE   — Restore/rollback/fix
6. VERIFY    — Health checks + smoke test
7. MONITOR   — Watch closely for 1-2 hours
8. DOCUMENT  — Timeline + postmortem
```

## Dependency Map

```
Frontend (Vercel)
    │
    ▼
Backend API (Render Web Service)
    │
    ├── PostgreSQL (Render Database)
    ├── Background Jobs (APScheduler)
    └── External APIs
        ├── Weather (Open-Meteo)
        └── Future: Payment, Email
```

## Critical vs Non-Critical

| Critical (must recover first) | Non-Critical (can wait) |
|-------------------------------|------------------------|
| Database | Advanced analytics |
| Authentication | Report generation |
| Core API | Email notifications |
| Device telemetry ingest | Webhook delivery |
| Billing data | Historical data |

## Recovery Drill Schedule

- **Monthly:** Verify backup exists and is recent
- **Quarterly:** Test restore to recovery environment
- **Annually:** Full disaster recovery drill

## Recovery Drill Checklist

- [ ] Select backup to restore
- [ ] Restore to separate environment
- [ ] Verify database schema complete
- [ ] Verify critical tables have data
- [ ] Start application against restored DB
- [ ] Run health checks
- [ ] Login as test user
- [ ] Verify dashboard loads
- [ ] Record RTO (time taken)
- [ ] Record RPO (data freshness)
- [ ] Document issues found
- [ ] Update recovery plan if needed
