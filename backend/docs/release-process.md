# SolarFlow — Production Release Process (STEP 56)

Filled in with real status as of Step 86 (2026-08-14). See
`docs/production-readiness-report.md` for the full synthesis and
Go/No-Go decision this feeds into.

## Release Checklist

### Pre-Deploy

- [ ] Release candidate frozen (no new features) — not yet declared; still mid-roadmap at Step 86
- [ ] Version tag created: `git tag v1.0.0` — **note:** an earlier `v1.0.0` tag already exists in this repo's history (predates Steps 77-86); a real release now needs a new tag, not a re-use of that one
- [x] All P0/P1 bugs fixed — `docs/operations/qa-report.md`: Critical 0, High 0
- [x] QA sign-off received — `docs/operations/qa-report.md`'s Go/No-Go: **GO**, with 2 documented residual risks
- [x] Security checklist passed — `docs/security-checklist.md`, corrected and re-verified in Step 86

### Environment Verification

- [ ] DATABASE_URL → Production database — **⚠️ CONFIRM IN RENDER DASHBOARD**
- [ ] JWT_SECRET → Unique production secret (not dev) — **⚠️ CONFIRM IN RENDER DASHBOARD**
- [ ] APP_ENV=production — **⚠️ CONFIRM IN RENDER DASHBOARD**
- [ ] DEBUG=false — **⚠️ CONFIRM IN RENDER DASHBOARD** (low-risk either way — see `production-launch-checklist.md`'s note on why)
- [ ] CORS_ALLOWED_ORIGINS → Production frontend URL only — **⚠️ CONFIRM IN RENDER DASHBOARD**
- [ ] All external API keys are production keys — **N/A**: the only real external dependency is the Open-Meteo weather API, which needs no API key
- [x] No dev/staging secrets in production — `.env` is gitignored, never committed; confirmed by Step 85's secrets scan finding zero real secrets in the repo

### Database

- [x] Production database backup — Render-managed automatic daily backups + PITR
- [ ] Backup verified (can restore) — **known, documented gap** (Step 83/85) — no restore has actually been executed and validated this session; infra/access constraints, not an oversight
- [x] Migrations reviewed for destructive changes — every migration this session was reviewed individually before applying; none drop columns/tables with real data
- [x] Migration rollback strategy documented — 59/59 migrations statically verified to have symmetric upgrade/downgrade (Step 85); live downgrade execution not performed (same access constraint as backup restore)

### Deploy

```bash
# Tag release
git tag v1.0.0
git push origin v1.0.0

# Render auto-deploys from main branch
# Or trigger manual deploy from Render dashboard
```

### Post-Deploy Verification

- [ ] `GET /health` → 200
- [ ] `GET /health/ready` → ready
- [ ] Swagger `/docs` accessible
- [ ] Login works
- [ ] Dashboard returns data
- [ ] Device telemetry ingests
- [ ] Analytics endpoint responds
- [ ] Notifications deliver
- [ ] Queue processing (worker alive)

### Smoke Test Script

```bash
# Health
curl https://YOUR_API_URL/health
curl https://YOUR_API_URL/health/ready

# Root
curl https://YOUR_API_URL/

# Swagger
curl -s https://YOUR_API_URL/docs | head -1

# Auth (should return 422, not 500)
curl -X POST https://YOUR_API_URL/api/v1/auth/login -H "Content-Type: application/json" -d '{}'
```

### Monitoring Verification

- [ ] Error tracking active
- [ ] Request logging working
- [ ] Alerts configured
- [ ] Backup schedule active

### Rollback Plan

If issues detected after deploy:

1. Check error rate and logs
2. If critical: trigger Render rollback to previous deploy
3. If database migration issue: assess data impact
4. Communicate status to team

### Frontend Connection

- [ ] Vercel NEXT_PUBLIC_API_URL = production backend URL
- [ ] Frontend redeployed with production API
- [ ] Login → Dashboard flow works in browser

---

## Post-Release Monitoring (First 24 Hours)

Monitor closely:
- Error rate (should stay < 1%)
- P95 latency (should stay under targets)
- Database connections (pool healthy)
- Queue depth (not growing unbounded)
- Worker success rate

## Release Complete

After 24 hours of stable operation:
- [ ] No critical issues
- [ ] Error rate normal
- [ ] Performance baseline captured
- [ ] Release notes published
- [ ] Team notified

**Status as of 2026-08-14: NOT independently confirmed.** A deploy for
commit `30370a4` (Step 83) timed out on Render (migration hang, no port
ever opened — see `alembic/env.py`'s `lock_timeout` fix, Step 84). Commits
since then (`5d61715` through the current Step 86 push) have not had their
Render deploy status confirmed back to this session. Don't treat the line
above as a claim that production is currently healthy — run the Post-Deploy
Verification steps above against the real URL before believing it.
