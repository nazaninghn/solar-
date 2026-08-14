# SolarFlow — Production Release Process (STEP 56)

## Release Checklist

### Pre-Deploy

- [ ] Release candidate frozen (no new features)
- [ ] Version tag created: `git tag v1.0.0`
- [ ] All P0/P1 bugs fixed
- [ ] QA sign-off received
- [ ] Security checklist passed

### Environment Verification

- [ ] DATABASE_URL → Production database
- [ ] JWT_SECRET → Unique production secret (not dev)
- [ ] APP_ENV=production
- [ ] DEBUG=false
- [ ] CORS_ALLOWED_ORIGINS → Production frontend URL only
- [ ] All external API keys are production keys
- [ ] No dev/staging secrets in production

### Database

- [ ] Production database backup taken
- [ ] Backup verified (can restore)
- [ ] Migrations reviewed for destructive changes
- [ ] Migration rollback strategy documented

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

**Status: PRODUCTION LIVE ✅**
