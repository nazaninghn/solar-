# SolarFlow Backend — Documentation Index

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

One entry point into everything documented about this backend, organized
by the categories Step 87 asked for. Files stay where they already are —
this is an index, not a folder restructure, since every doc written this
session cross-references others by relative path (`docs/operations/...`,
`../operations/...`), and moving files would silently break every one of
those links for no real benefit.

**Frontend and User Guide categories are intentionally absent** — the
frontend is a separate Vercel-hosted repository this backend has no
visibility into; there is no end-user-facing documentation to write from
inside an API-only repo. Both are N/A by architecture, not missing by
oversight.

## 01 — Overview
- [`../README.md`](../README.md) — top-level project readme
- [`PROJECT_CLOSURE.md`](PROJECT_CLOSURE.md) — v1.0.0 project summary
- [`ROADMAP_V2.md`](ROADMAP_V2.md) — what's planned beyond v1.0.0
- [`../CHANGELOG.md`](../CHANGELOG.md) — version history, now including Steps 77-86

## 02 — Architecture
- [`architecture.md`](architecture.md) — system diagram, component overview
- [`architecture-decisions.md`](architecture-decisions.md) — **new (Step 87)**: real ADRs (why APScheduler not Celery, why no cache, why single-instance, etc.), consolidated from decisions previously scattered as inline code comments

## 03 — Backend
- [`api-contract.md`](api-contract.md) — API design conventions
- Live OpenAPI schema: `/docs` (Swagger) and `/redoc` on any running instance
- `app/modules/` — one self-contained module per feature; each module's own docstrings are the ground truth for its business logic

## 04 — Database
- [`setup.md`](setup.md)'s Database section — migrations, rollback commands
- Schema: `app/models/` (root-level, shared) + each `app/modules/*/models.py`
- Migration history: `alembic/versions/` — one file per schema change, all with real `upgrade()`/`downgrade()` pairs (verified symmetric for all 59+ migrations in Step 85)

## 05 — Security
- [`security/zero-trust-architecture.md`](security/zero-trust-architecture.md) — the real security posture: what's already zero-trust-shaped, what Step 82 closed, what's N/A
- [`security-checklist.md`](security-checklist.md) — item-by-item hardening checklist, corrected in Step 86
- [`security-audit-final.md`](security-audit-final.md) — point-in-time audit record
- [`policies/access-policy.md`](policies/access-policy.md) — RBAC model, least privilege
- [`policies/README.md`](policies/README.md) — compliance policy index (data inventory, retention, vendor governance)

## 06 — Infrastructure & Deployment
- [`deployment-guide.md`](deployment-guide.md) — Render deployment mechanics
- [`production-launch-checklist.md`](production-launch-checklist.md) — filled in with real status (Step 86)
- [`release-process.md`](release-process.md) — release checklist, smoke test script, rollback plan
- [`ci-cd-pipeline.md`](ci-cd-pipeline.md) — pipeline design doc; the real implementation is `.github/workflows/ci.yml` (Step 85 — this doc was "conceptual" for years before that)

## 07 — Monitoring, Logging & Alerts
- [`operations/monitoring.md`](operations/monitoring.md) — what's monitored
- [`operations/observability-overview.md`](operations/observability-overview.md) — SLI/SLO, tracing, synthetic monitoring
- [`operations/performance-scalability-report.md`](operations/performance-scalability-report.md) — real load-test results, the connection-pool bug found and fixed (Step 84)
- Real alerting jobs (what fires, how often, on what threshold): `docs/production-readiness-report.md`'s 86.11-86.14 section has the current authoritative list

## 08 — Runbooks & Troubleshooting
- [`runbooks.md`](runbooks.md) — **current, authoritative** operational runbooks (DB down, weather API down, scheduler issues, device offline, high error rate) — written with exact endpoint references
- [`operations/runbooks.md`](operations/runbooks.md) — older, partially superseded (now cross-references the file above; kept for Storage Full / Security Incident, which aren't duplicated elsewhere)
- [`troubleshooting.md`](troubleshooting.md) — general troubleshooting FAQ
- [`operations/incidents.md`](operations/incidents.md) — incident severity levels, lifecycle, postmortem requirement

## 09 — Disaster Recovery & Business Continuity
- [`operations/disaster-recovery.md`](operations/disaster-recovery.md) — RPO/RTO targets, backup policy, 5 disaster scenarios with concrete recovery steps
- [`policies/business-continuity-plan.md`](policies/business-continuity-plan.md) — who notifies whom, communication templates, escalation

## 10 — Testing & QA
- [`operations/qa-report.md`](operations/qa-report.md) — full Step 85 QA synthesis: SAST/dependency/secrets scan results, concurrency/idempotency findings, Go/No-Go
- [`qa-report-template.md`](qa-report-template.md) — template for future QA cycles

## 11 — Business Intelligence
- [`bi/metric-dictionary.md`](bi/metric-dictionary.md) — what every BI metric means and how it's computed

## 12 — AI/ML
- [`ai/ai-ml-readiness-assessment.md`](ai/ai-ml-readiness-assessment.md) — honest assessment: every "AI" feature today is rule-based/statistical, not trained ML; real data-readiness numbers; ranked future use cases

## 13 — Production Readiness
- [`production-readiness-report.md`](production-readiness-report.md) — Step 86's full synthesis across Steps 77-86, with Go/No-Go decision
- [`final-architecture-review.md`](final-architecture-review.md) — **new (Step 88)**: final cross-cutting review across all 9 architecture dimensions (scalability, reliability, security, data, integration, performance, cost, technical debt) with a formal Architecture Approved decision

## 14 — Change Management
- [`../CHANGELOG.md`](../CHANGELOG.md) — version history
- [`known-issues.md`](known-issues.md) — **new (Step 87)**: consolidated open items with owner/status/expected-fix, pulled from the QA and production-readiness reports' risk-acceptance sections

## 15 — Onboarding & Local Development
- [`onboarding.md`](onboarding.md) — day-1/2/3 path for a new developer
- [`setup.md`](setup.md) — environment variables, local setup, code-quality tooling (updated Step 87 with Step 84/85's additions)

## Sensitive Information

Scanned with `detect-secrets` against the same baseline CI uses (Step 87)
— clean. No passwords, API keys, tokens, or private keys in this
documentation set.

## Keeping This Index Current

Add a line here in the same commit that adds a new doc file — an index
that drifts from reality is worse than no index, since it actively
misdirects instead of just being silent.
