# SolarFlow — Incident Management

## Incident Severity

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | System down, data loss, security breach | Immediate |
| P1 | Major feature broken, payment failure | < 1 hour |
| P2 | Degraded performance, non-critical bug | < 4 hours |
| P3 | Minor issue, cosmetic | Next business day |

## Incident Lifecycle

```
Detect → Acknowledge → Investigate → Mitigate → Resolve → Postmortem
```

### 1. Detect
- Monitoring alert fires
- User reports issue
- Error spike in logs

### 2. Acknowledge
- Assign owner
- Start timeline
- Communicate status

### 3. Investigate
- Check logs (use request_id)
- Check recent deploys
- Check external services
- Identify root cause

### 4. Mitigate
- **First priority: restore service**
- Rollback if deploy caused it
- Kill switch if feature caused it
- Scale if capacity issue

### 5. Resolve
- Confirm fix deployed
- Verify health checks pass
- Monitor for regression
- Update status

### 6. Postmortem
- What happened?
- Timeline
- Root cause (5 Whys)
- Impact (users affected, duration)
- What we'll do to prevent recurrence
- Action items with owners

## Communication

During incident:
- Team channel updated every 15 min
- Stakeholders notified for P0/P1

After resolution:
- Summary sent to team
- Postmortem within 48 hours for P0/P1

## Golden Rules

1. **Mitigate first, investigate later**
2. **No blame** — focus on prevention
3. **Document everything** — timeline is crucial
4. **Every P0/P1 gets a postmortem**
5. **Add regression tests** for every incident
