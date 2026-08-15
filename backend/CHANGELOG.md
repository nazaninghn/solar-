# Changelog

## Unreleased (Steps 77-86, 2026-08-14)

Production-readiness hardening pass — advanced observability, cost
governance, compliance, BI, AI/ML readiness, zero-trust security,
disaster recovery, performance, QA/CI, and final production-readiness
synthesis. Each step's investigation found substantial pre-existing
schema/scaffolding from the v1.0.0 build below that had never been wired
up — this pass is mostly "make it real," not new surface area.

- **Observability** (Step 77): real anomaly detection, SLI/SLO tracking,
  on-call rotation, postmortem workflow, trace propagation, synthetic
  monitoring, telemetry retention
- **FinOps** (Step 78): `TenantQuota` enforcement wired into resource
  creation, `APIUsageMetric`/`CapacityMetric` populated with real
  measurements, infrastructure cost model, budget alerts
- **Business Intelligence** (Step 80): real signup funnel, retention/
  cohort analysis, revenue metrics against real billing schema,
  organization segmentation, KPI alerts
- **Compliance & Governance** (Step 79): data subject rights (export/
  deletion), legal hold mechanism, security event correlation, vendor
  governance tracking, full policy documentation set
- **AI/ML Readiness** (Step 81): honest assessment (every "AI" feature
  is rule-based/statistical, not ML), real data-readiness scoring,
  `ForecastModelRegistry` populated, forecast drift detection
- **Zero-Trust Security** (Step 82): security event logging wired to
  real call sites, general API rate limiting, `APIKey` model wired into
  a real auth mechanism, fixed a JWT `jti` bug that silently defeated
  refresh-token reuse detection
- **Disaster Recovery** (Step 83): real RPO/RTO targets seeded, drill
  lifecycle tracking, business continuity/communication plan, fixed a
  bug where `complete_drill` evaluated every drill against the wrong
  target
- **Performance & Scalability** (Step 84): real load test found a
  connection-pool bottleneck causing 6-23% error rates under load —
  fixed (14-16x P95 improvement), 2 composite indexes added, a second
  real bug found (capacity-metric miscalculation) and fixed
- **Testing & QA** (Step 85): real CI/CD pipeline built (lint, SAST,
  dependency scan, secrets scan, test, build verification — previously
  documented as "conceptual," never built), a real concurrency bug
  found and fixed (tenant quota check-then-act race)
- **Production Readiness** (Step 86): `AccountLockout` wired into login
  (existed since v1.0.0, never called), a real timezone bug fixed
  (Postgres session timezone vs. the app's UTC timestamps disagreeing
  on "today" for part of each day, affecting every day-grouped query),
  existing launch checklists filled in with verified status

## v1.0.0 (2026-08-14)

### Backend Modules (Steps 32-53)
- Energy Control & Command Orchestration
- Device Gateway & MQTT Adapters
- Production Data Pipeline & Time-Series Storage
- Energy Forecasting Engine (Solar/Load/Net)
- Smart Optimization & Recommendation System
- Financial Engine, Tariffs & Settlement
- Control Center & Command Orchestration
- IoT Gateway & MQTT Messaging
- Alerts & Incident Management
- Data Quality & Observability
- Events, Notifications & Webhooks
- Billing, Subscriptions & Metering
- Advanced Analytics & KPI Engine
- Admin Panel & Platform Management
- Security Hardening & Audit
- Production Monitoring & Incident Management
- Testing & Production Launch
- Disaster Recovery & Business Continuity
- Performance & Scalability (Circuit Breaker, Quotas)
- API Documentation & Developer Experience

### Infrastructure
- 97 database tables
- Alembic migrations (single-head chain)
- FastAPI with structured middleware
- Security headers, rate limiting, CORS
- Health checks (liveness + readiness)
- Render deployment ready

### Documentation
- Architecture diagram
- Setup guide
- Onboarding guide
- API contract
- Security checklist
- Production launch checklist
- Troubleshooting guide
- Contributing guide
