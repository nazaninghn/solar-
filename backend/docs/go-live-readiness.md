# Go-Live Readiness (STEP 89)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## What This Document Is — and Isn't

Everything **technically verifiable from this codebase** is checked below,
with real evidence. What it can't do — and won't fabricate — is the actual
launch event: triggering the real Render deploy, confirming it went live,
getting real stakeholders to actually say "go," and declaring a real
system "launched" when this is a pre-launch codebase with no production
users yet. Those are genuinely your calls, not something completable by
reading code.

## 89.1 — Final Go-Live Checklist

| Item | Status | Evidence |
|---|---|---|
| Release Candidate approved | ⚠️ **Not yet declared** | No commit has been tagged as a Release Candidate; see "Declaring a Release Candidate" below |
| QA Sign-Off | ✅ GO | `docs/operations/qa-report.md` — 216/216 (now 219/219 after Step 86), 0 Critical/High |
| Security Sign-Off | ✅ Pass | `docs/security/zero-trust-architecture.md`, `docs/security-checklist.md` (corrected Step 86) |
| Architecture Approved | ✅ Approved | `docs/final-architecture-review.md` (Step 88) — 0 critical architecture risk |
| Backup Verified | ⚠️ Partial | Render's automatic backup exists; **restore has never been live-tested** (`docs/known-issues.md`) |
| Rollback Verified | ✅ Real | Render dashboard → previous deploy → redeploy; documented in `docs/release-process.md`; the actual Step 83→84 deploy incident is real evidence the *process* (old version stays serving) works even when a new deploy hangs |
| Monitoring Ready | ✅ Real | 5 real alerting jobs registered (`docs/production-readiness-report.md`'s 86.11-86.14), real P50/P95/P99 tracking |
| Alerting Ready | ✅ Real | Same as above — not aspirational, verified firing in tests across Steps 78-84 |
| On-Call Ready | ⚠️ **Schedule mechanism is real, roster is not confirmed** | `OnCallSchedule` (Step 77) is real infrastructure; whether it currently has real people assigned to real time windows is org information this review can't see |
| Documentation Ready | ✅ Complete | `docs/README.md` indexes all 36 docs; Step 87 confirmed no sensitive data leaked into any of them |

## 89.2 — Freeze

Not currently in effect — this review is being written *during* active
development (Steps 77-88 all landed today). A real code/config/DB-change
freeze is something to declare deliberately, at a specific commit, when
you're ready to stop adding scope — not something this document can
declare on your behalf mid-session.

## 89.3 — Final Backup

Render's automatic daily backup covers this passively. There's no action
this review can trigger — Render backups run on Render's own schedule,
not on-demand from this codebase. If you want a backup taken at a
specific moment right before a deploy, that's a Render dashboard action.

## 89.4-89.5 — Deployment & Smoke Test

**Built this step, real and runnable:** `scripts/smoke_test.py` — 10
checks (app responds, health, readiness, Swagger, auth validation, and a
full register→login→core-workflow round trip), verified passing 10/10
against the local dev server. Run it against the real production URL
right after any deploy:

```bash
python scripts/smoke_test.py --base-url https://your-service.onrender.com
```

It exits non-zero if anything fails, so it can gate a deploy script or
just be run by hand and read.

## 89.6-89.7 — Monitoring Window & Incident Decision

Process is documented (`docs/release-process.md`'s Post-Release Monitoring
section: watch error rate, P95 latency, DB connections, worker success for
the first 24 hours). This review can't *watch* anything — there's no
running production instance this session has visibility into right now.

## 89.8 — Launch Validation

**Cannot be completed by this review — there is no real production traffic
yet.** This system is pre-launch. "Users, requests, errors, latency,
business transactions" against real data is something to check *after* a
real go-live, not something to fabricate now. Revisit this section with
real numbers once there's real traffic to look at.

## 89.9 — Stakeholder Confirmation

**Genuinely not something this review can do.** Technical sign-off is
real and documented above. Operations and Business sign-off need real
people to actually say so.

## Declaring a Release Candidate

If you want to move forward, the concrete next step is: pick the current
commit (`eb6b60c` as of this writing, or whatever `main` is at when you
read this), tag it (`git tag v1.1.0` or similar — note `docs/release-
process.md` flags that an earlier `v1.0.0` tag already exists in this
repo's history, so don't reuse it), and treat that tag as frozen. From
there, the remaining real work before an actual go-live is:

1. Fill in `docs/production-readiness-report.md`'s ownership table with
   real names (the one item every review this session has flagged as
   genuinely open, not fabricatable)
2. Confirm Render's dashboard environment variables (the "⚠️ CONFIRM IN
   RENDER DASHBOARD" items throughout `docs/production-launch-
   checklist.md`)
3. Deploy, then run `scripts/smoke_test.py` against the real URL
4. Watch the first 24 hours per `docs/release-process.md`
5. Get real stakeholders to actually confirm — this document can't do
   that step for you
