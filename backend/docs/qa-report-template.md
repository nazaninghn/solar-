# SolarFlow — QA Report Template

## Summary

| Metric | Value |
|--------|-------|
| Date | YYYY-MM-DD |
| Environment | QA / Staging |
| Build Version | commit SHA |
| Total Tests | X |
| Passed | X |
| Failed | X |
| Blocked | X |
| Skipped | X |

## Critical Path Results

| Journey | Status |
|---------|--------|
| Register → Login → Dashboard | ⬜ |
| Create Factory → Add Device → Telemetry | ⬜ |
| Forecast → Recommendation → Approval | ⬜ |
| Billing → Invoice → Payment | ⬜ |
| Admin → Users → Audit | ⬜ |

## Security Tests

| Test | Status |
|------|--------|
| Tenant Isolation | ⬜ |
| IDOR Protection | ⬜ |
| Rate Limiting | ⬜ |
| Token Security | ⬜ |
| Input Validation | ⬜ |
| Admin Access Control | ⬜ |

## Failure Tests

| Test | Status |
|------|--------|
| Database Timeout | ⬜ |
| Queue Failure | ⬜ |
| Worker Failure | ⬜ |
| External API Timeout | ⬜ |
| Duplicate Events | ⬜ |

## Open Bugs

| ID | Severity | Description | Blocker? |
|----|----------|-------------|----------|
| | P0/P1/P2/P3 | | Yes/No |

## Release Decision

- [ ] All P0 bugs fixed
- [ ] All P1 bugs fixed or accepted
- [ ] Security tests passing
- [ ] Performance acceptable
- [ ] Backup verified
- [ ] Rollback tested

**Decision:** RELEASE / HOLD / FIX REQUIRED

**Sign-off:** ________________ Date: ________
