# SolarFlow — Monitoring Guide

## What We Monitor

### API Health
- Availability: `/health` returns 200
- Readiness: `/health/ready` checks DB
- Error rate: 5xx percentage
- Latency: P50, P95, P99

### Database
- Connection pool (active/idle/max)
- Query latency
- Storage usage + growth rate
- Lock contention
- Slow queries

### Queue & Workers
- Queue depth (jobs waiting)
- Processing rate
- Failed job count
- Worker heartbeat
- Dead letter queue size

### External Services
- Weather API availability + latency
- Payment provider status
- Email delivery success rate

### Business Metrics
- Active organizations
- Online devices
- Telemetry ingestion rate
- Forecast generation success
- Recommendation acceptance rate

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| API error rate | > 2% | > 5% |
| P95 latency | > 1s | > 3s |
| DB connections | > 70% | > 90% |
| Queue depth | > 100 | > 500 |
| Worker failures | > 5/min | > 20/min |
| Storage usage | > 70% | > 90% |

## Daily Checks

- [ ] API health green
- [ ] Error rate normal
- [ ] Queue processing
- [ ] Workers alive
- [ ] Backup completed
- [ ] No critical alerts

## Weekly Review

- Error trends
- Latency trends
- Database growth
- Cost trends
- Security events
- Dependency updates

## Dashboards

- System Health: `/api/v1/admin/monitoring/overview`
- Security: `/api/v1/admin/security/events/summary`
- Data Quality: `/api/v1/factories/{id}/observability/health`
