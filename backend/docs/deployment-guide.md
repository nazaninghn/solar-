# SolarFlow — Production Deployment Guide (STEP 62)

## Release Flow

```
Code → PR → CI → Staging → Approval → Production → Monitor
```

## Versioning

Semantic versioning: `vMAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Pre-Deployment Checklist

- [ ] CI passed (lint + tests + security)
- [ ] Staging validated
- [ ] Database migration reviewed
- [ ] Backup verified (recent + restorable)
- [ ] Rollback strategy documented
- [ ] Monitoring ready
- [ ] Release notes written

## Render Deployment

### Auto-Deploy (Normal)
Push to `main` → Render auto-deploys → migrations run → health check

### Manual Deploy
Render Dashboard → Select service → Manual Deploy → Choose commit

### Start Command
```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Post-Deployment

### Immediate (0-5 min)
- [ ] `GET /health` → 200
- [ ] `GET /health/ready` → ready
- [ ] Login works
- [ ] No 500 errors in logs

### Short-term (5-30 min)
- [ ] Error rate stable
- [ ] Latency normal
- [ ] Queue processing
- [ ] Workers alive

### Business Verification
- [ ] Dashboard loads with data
- [ ] Device telemetry ingesting
- [ ] Analytics responding
- [ ] Billing endpoints working

## Rollback

### When to Rollback
- Health check fails
- Error rate > 5%
- Critical feature broken
- Data corruption detected
- Security vulnerability found

### How to Rollback
1. Render Dashboard → Deploys → Select previous successful deploy → Redeploy
2. If database migration issue: assess if rollback migration needed
3. Monitor after rollback

### Database Rollback
- Simple migrations: `alembic downgrade -1`
- Complex/destructive: forward-fix only (no automatic rollback)
- Always have backup before risky migrations

## Hotfix Process

```
Critical Bug Found
    ↓
Create hotfix branch from main
    ↓
Fix + minimal test
    ↓
PR with "hotfix" label
    ↓
Fast review
    ↓
Merge + deploy
    ↓
Verify fix
    ↓
Monitor
```

## Migration Safety

### Safe Migrations
- ADD column (nullable)
- ADD index
- CREATE table

### Risky Migrations (require review)
- DROP column
- RENAME column
- ALTER type
- Data transformation

### Strategy for Risky Changes
1. Backup database
2. Add new column/table
3. Deploy code that writes to both
4. Migrate data
5. Deploy code that reads from new
6. Remove old (later release)

## Release Record

After each deployment, record:
| Field | Value |
|-------|-------|
| Version | vX.Y.Z |
| Commit | SHA |
| Date | YYYY-MM-DD HH:MM |
| Deployer | Name |
| Migrations | Yes/No |
| Status | Success/Rollback |
| Notes | Any issues |

## Deployment Metrics (Goals)

| Metric | Target |
|--------|--------|
| Deploy frequency | Weekly+ |
| Lead time | < 1 day |
| Change failure rate | < 10% |
| Recovery time | < 30 min |
