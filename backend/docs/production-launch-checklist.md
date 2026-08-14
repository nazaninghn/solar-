# SolarFlow — Production Launch Checklist

## Pre-Launch

- [ ] All P0/P1 bugs fixed
- [ ] API Contract finalized and documented
- [ ] OpenAPI/Swagger complete
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Security tests passing
- [ ] Tenant isolation verified
- [ ] Load test completed

## Environment

- [ ] Production DATABASE_URL configured
- [ ] JWT_SECRET rotated (not dev value)
- [ ] CORS_ALLOWED_ORIGINS set to production frontend URL
- [ ] APP_ENV=production
- [ ] DEBUG=false
- [ ] Email provider configured
- [ ] Payment provider configured (if applicable)

## Database

- [ ] Migrations applied successfully
- [ ] Backup configured and tested
- [ ] RPO/RTO defined
- [ ] Connection pool sized appropriately

## Deployment

- [ ] Render Web Service configured
- [ ] Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path: `/health`
- [ ] Auto-deploy from main branch enabled
- [ ] Rollback strategy documented

## Post-Deploy

- [ ] `GET /health` returns 200
- [ ] `GET /health/ready` returns ready
- [ ] Swagger `/docs` accessible
- [ ] Login works
- [ ] Dashboard loads data
- [ ] No 500 errors in logs

## Monitoring

- [ ] Error tracking enabled
- [ ] Request logging enabled
- [ ] Security events tracking active
- [ ] Alert system operational
- [ ] Backup monitoring active

## Documentation

- [ ] API documentation published
- [ ] Deployment guide complete
- [ ] Rollback guide complete
- [ ] Incident response guide complete
