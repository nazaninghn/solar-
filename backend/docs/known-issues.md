# Known Issues

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

Real, currently-open items — consolidated from `docs/operations/
qa-report.md` and `docs/production-readiness-report.md`'s risk
acceptance sections rather than duplicated. Nothing here is Critical or
High severity (that bar is 0 per this project's own QA policy); everything
below has a documented reason it wasn't closed, not a silent gap.

| Issue | Impact | Workaround | Owner | Status | Expected Fix |
|---|---|---|---|---|---|
| Backup restore never live-tested | Medium — Render's managed backups exist, but an actual restore has never been executed and validated this session | Manual quarterly drill process is fully tracked (RPO/RTO targets, drill lifecycle, checklist — Step 83); execute one for real before this becomes the first real incident | `[TBD]` | Open | Next scheduled DR drill |
| No periodic secret rotation | Low — no known compromise, this is a hardening gap | Rotation-on-compromise is documented (`docs/operations/disaster-recovery.md`); `APIKey.expires_at` is enforced when set | `[TBD]` | Open | When there's a real ops calendar to schedule it against |
| Login latency under load (P95 1.2-5.8s, target <300ms) | Medium — a real, measured finding (Step 84); 0% error rate at every concurrency tested, so this is slow, not broken | None needed today; password hashing cost is a deliberate security tradeoff (ADR-10 in `docs/architecture-decisions.md`), not a bug | `[TBD]` | Open, deliberately unresolved | Needs an explicit decision (async-friendly hashing vs. accept the cost), not a silent patch |
| No full DAST scanner run | Low — compensating controls verified directly (security headers present on every response, error responses don't leak stack traces — both tested, not assumed) | None needed at current risk level | `[TBD]` | Open | Before a larger/public launch |
| No live production user-access review | Low — RBAC design is sound (Step 79 fixed a real cross-tenant escalation), but nobody has audited who currently holds what role in the live system | N/A — requires real production data this session has no visibility into | `[TBD]` | Open | First post-launch access review |
| Ownership table unfilled (`docs/production-readiness-report.md`) | Low technically, real operationally — an incident with no named owner is slower to resolve | N/A | User | **Open — blocks declaring a Release Candidate** | Before Step 89 (Go-Live) |
| No custom domain / no email or payment provider | N/A, not a defect | Documented as deliberate scope, not gaps — Render's default subdomain works, and nothing in the product currently depends on email delivery or payments | N/A | By design | Revisit if/when those features are actually built |

## How This List Gets Maintained

Add an issue here the same day it's found and accepted (not fixed) —
the same day a step's own investigation surfaces something real but
out-of-scope for that step, per this project's established pattern this
session (e.g. Step 84 finding the login-latency issue while testing
something else entirely). Remove a row only when the fix actually ships,
not when it's merely scheduled.
