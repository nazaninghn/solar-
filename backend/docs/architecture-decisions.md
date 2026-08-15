# Architecture Decision Records

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

Real decisions made across this project's history, consolidated from
where they previously only lived as inline code comments — this is a
single place to find *why*, not a duplicate of what the code already
shows. Each follows Decision → Context → Options → Chosen → Reason →
Trade-offs.

## ADR-1: In-process APScheduler, not Celery/Redis

**Context:** Every background job (aggregation, alerts, forecasting,
retention, security correlation, performance checks, etc.) needs
scheduling.
**Options:** Celery + Redis (separate broker + worker processes) vs.
APScheduler running inside the same FastAPI process.
**Chosen:** APScheduler, in-process (`app/jobs/scheduler.py`).
**Reason:** At this project's scale, a single Render web-service
instance already runs everything; Redis would be a new infrastructure
dependency (cost + operational surface) for a queueing problem this
project doesn't have — every job here is scheduled (cron/interval), not
triggered by unpredictable event volume.
**Trade-offs:** No distributed workers, no true task retries across
multiple instances, jobs share the same process's resources as the web
server. Revisit if this ever needs more than one instance or genuinely
unpredictable/bursty background work.

## ADR-2: JWT-only auth, no server-side sessions

**Context:** How to authenticate API requests.
**Options:** Server-side session store (Redis/DB-backed) vs. stateless
JWT access tokens.
**Chosen:** JWT access tokens (short-lived, 30 min default) + rotating
refresh tokens, no session store.
**Reason:** Stateless tokens mean no shared session store is needed
(consistent with ADR-1's "no Redis" choice), and every request is
independently, freshly verified against the database (`get_current_user`
re-fetches the user every time) — this turned out to already be
zero-trust-shaped (Step 82) without having designed it as such
originally.
**Trade-offs:** Revoking a still-valid access token before its natural
expiry isn't instant (max 30 min exposure window) — only refresh tokens
and account status are checked on every request; a compromised *access*
token is live until it expires. Deliberate: instant revocation would
need a token blocklist, which reintroduces the server-side state this
decision avoided.

## ADR-3: No caching layer

**Context:** `docs/operations/scalability.md` (Step 58) documented what
*should* be cached (dashboard KPIs, org metadata, forecast results) —
none of it was ever built.
**Options:** Add Redis/in-memory caching for hot read paths vs. address
performance bottlenecks as they're actually found.
**Chosen:** No caching layer, at least for now.
**Reason:** Step 84's real load test found the actual bottleneck under
concurrent load was connection pool exhaustion, not database query cost
— fixing the pool (a config change) resolved it completely (0% errors,
14-16x P95 improvement) without needing cache invalidation complexity.
**Trade-offs:** If a future load test shows the *database itself* (not
the pool) as the limiting factor, this decision should be revisited —
not before, since building cache invalidation for a problem that isn't
measured yet is exactly the kind of speculative complexity this
project's own conventions warn against.

## ADR-4: Single Render instance, no autoscaling/Kubernetes

**Context:** How much infrastructure to provision for current traffic.
**Options:** Multi-instance with a load balancer, Kubernetes, or a
single Render web service.
**Chosen:** Single instance, confirmed via Step 84's load test that it
handles 150 concurrent requests cleanly once the connection pool was
tuned.
**Reason:** Real infrastructure has real cost; provisioning for load
this project doesn't have yet is speculative spend, not resilience.
**Trade-offs:** No redundancy if the single instance goes down — Render
restarts a crashed process automatically, but there's a real gap between
crash and restart. No horizontal scaling if traffic genuinely exceeds
what one instance (even well-tuned) can serve. Revisit when real traffic
data says so, not preemptively.

## ADR-5: In-memory metrics reservoir, not Prometheus/Grafana

**Context:** Need P50/P95/P99 latency and request metrics.
**Options:** Stand up a Prometheus + Grafana stack vs. an in-process
bounded reservoir of recent request durations.
**Chosen:** In-memory reservoir (`app/core/metrics.py`, 2000-sample
bounded deque), exposed via `GET /api/v1/system/metrics`.
**Reason:** Same reasoning as ADR-1/ADR-3 — a separate timeseries
service is real operational overhead this project's single-instance
scale doesn't justify yet, and a 2000-sample reservoir gives real
percentiles (not just averages) without it.
**Trade-offs:** Metrics don't survive a process restart, and don't
aggregate across instances if this ever becomes more than one. Revisit
alongside ADR-4 if this stops being single-instance.

## ADR-6: Rule-based/statistical "AI" features, not trained ML

**Context:** The product markets recommendations, forecasting, and
anomaly detection as "AI-powered."
**Options:** Build/train real ML models vs. ship well-reasoned
rule-based and statistical approaches first.
**Chosen:** Rule-based (recommendation engine's weighted scoring),
statistical baseline (forecasting's historical-average + adjustment),
and statistical process control (anomaly detection's 2.5σ threshold) —
confirmed via Step 81's investigation that this was always the honest
state, not something that quietly regressed from an ML system.
**Reason:** A defensible, explainable, and *already accurate enough*
approach shipped faster than a training pipeline this project has no
data-readiness for yet (Step 81 found essentially zero factories had
crossed the 90-day minimum for a real baseline comparison).
**Trade-offs:** Ceiling on prediction accuracy that only real ML would
raise. Explicitly not "fixed" in Step 81 per the scope decision that
step's investigation surfaced — revisit once real data volume justifies
it (see `docs/ai/ai-ml-readiness-assessment.md`'s ranked use-case list).

## ADR-7: Render-managed backups are the system of record; no app-level backup layer

**Context:** Step 83 asked whether to build an independent, app-level
backup mechanism (e.g. periodic `pg_dump`) alongside Render's own
managed Postgres backups.
**Options:** Add a second, independently-verifiable backup layer vs.
rely entirely on Render's managed backups and operationalize the
*process* around them (RPO/RTO targets, drill tracking).
**Chosen:** Render-managed only; Step 83 built real RPO/RTO targets and
drill lifecycle tracking around that single source of truth.
**Reason:** A second backup pipeline running inside the same
single-instance web service adds real CPU/disk/schedule overhead for
redundancy this project's risk tolerance doesn't currently require —
explicit user decision at the time (see Step 83's session record).
**Trade-offs:** A Render-account-level failure has no independent
mitigation. Backup *restore* has also never been live-tested this
session (access constraint, not a decision) — see Known Issues.

## ADR-8: Ruff configured to exclude 3 rule categories, not run with raw defaults

**Context:** Step 85 ran `ruff check` for the first time — raw defaults
produced 756 findings, the overwhelming majority false positives for
this specific codebase.
**Options:** Fix/suppress each finding individually, or configure ruff's
rule selection to match what this codebase's real patterns are.
**Chosen:** `pyproject.toml` selects `E4/E7/E9/F/I` and explicitly
excludes `F821` (SQLAlchemy's `Mapped["Factory"]` string forward
references, used throughout `app/models/` to avoid circular imports —
not real undefined names) and `E711`/`E712` (SQLAlchemy overloads
`Column.__eq__` to build SQL — `== None` becomes `IS NULL`; ruff's
suggested `is None` fix would silently stop building a SQL clause at
all). `B008` (flake8-bugbear) was never selected, since it flags
FastAPI's required `Depends(...)` default-argument pattern on ~580 real,
correct call sites.
**Reason:** Verified each exclusion against real findings before adding
it — this isn't "turn off anything inconvenient," it's "these three rule
categories are structurally incompatible with an ORM/framework-heavy
codebase," confirmed case by case.
**Trade-offs:** A genuine SQLAlchemy forward-reference typo (a real
`Mapped["Fctory"]` misspelling, say) wouldn't be caught by ruff anymore
— but it would fail loudly at import time regardless, since SQLAlchemy
resolves those strings at mapper-configuration time.

## ADR-9: Two-status-code tenant isolation (404 vs. 403)

**Context:** How to respond when a user requests a resource (e.g. a
factory) they can't access.
**Options:** Always 403 (consistent "forbidden" semantics) vs.
distinguishing cross-organization access (404) from
same-organization-but-unassigned access (403).
**Chosen:** 404 for cross-organization requests (a different tenant's
data doesn't even reveal that the ID exists), 403 for same-org access
the specific user isn't scoped to (the organization itself has a
legitimate relationship to the resource, so its existence isn't secret
from this user the way another tenant's data would be).
**Reason:** Confirmed explicitly with the user when this was introduced
(Step 24) — this is a deliberate distinction, not an inconsistency.
**Trade-offs:** Slightly more complex authorization logic
(`get_accessible_factory` checks organization match before per-user
scoping) than a single uniform status code would need.

## ADR-10: Password hashing cost — a measured tradeoff, deliberately not "fixed"

**Context:** Step 84's real load test found login P95 latency (1.2-5.8s
under load) well above the documented `<300ms` target — but with 0%
errors at every concurrency level tested.
**Options:** Reduce Argon2/bcrypt hashing cost to improve latency, or
leave it as-is.
**Chosen:** Left unchanged.
**Reason:** Password hashing is deliberately expensive — that's the
security property, not a bug. Trading it away for latency without being
asked to would be a real security regression disguised as a performance
fix.
**Trade-offs:** Slow login under load remains a real, documented,
unresolved finding (see `docs/operations/performance-scalability-
report.md`) — flagged for a future step to weigh explicitly (e.g.
async-friendly hashing, or accepting the latency as the cost of the
security property) rather than silently patched here.
