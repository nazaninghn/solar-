# Compliance & Governance (STEP 79)

## Policy Index

| Policy | Owner | Version | Review Date |
|---|---|---|---|
| [Personal Data Inventory](personal-data-inventory.md) | Engineering | 1.0 | 2027-02-14 |
| [Retention Policy](retention-policy.md) | Engineering | 1.0 | 2027-02-14 |
| [Access Policy](access-policy.md) | Engineering | 1.0 | 2027-02-14 |
| Incident Policy | See [docs/operations/incidents.md](../operations/incidents.md) | — | — |
| Security Policy | See [docs/operations/observability-overview.md](../operations/observability-overview.md) + `app/modules/security/` | — | — |
| [Vendor Policy](vendor-policy.md) | Engineering | 1.0 | 2027-02-14 |
| Backup Policy | See `backup_records` table, `app/modules/security/models.py` | — | — |

## Compliance Matrix (79.3)

| Requirement | Implementation | Evidence | Status |
|---|---|---|---|
| Privacy | Personal data inventory, self-service export/deletion | `app/modules/auth/data_rights.py`, tests in `tests/test_step79_compliance.py` | ✅ |
| Access Control | Role/permission matrix, tenant isolation, least privilege | `app/auth/permissions.py`, `app/core/dependencies.py`, `tests/integration/test_tenant_isolation.py` (8/8 real assertions, was placeholder before this step) | ✅ |
| Retention | Automated purge jobs with legal hold override | `app/jobs/retention_jobs.py`, `app/modules/compliance/` | ✅ |
| Audit | 3 audit-log models + security event log, immutable | `AuditLog`, `AdminAuditLog`, `RecommendationAuditLog`, `SecurityEvent` | ✅ |
| Security | Lockout, SSRF/path-traversal/mass-assignment guards, event correlation | `app/modules/security/` | ✅ |
| Tenant Isolation | Organization boundary + factory-level scoping, tested | `app/core/dependencies.py`, real cross-tenant tests (this step fixed a genuine cross-tenant vulnerability found while writing them — see `app/modules/admin/router.py`) | ✅ |
| Consent Management | N/A — no consent-requiring processing exists in this B2B product | — | Not applicable, documented decision |
| Data Residency | Single-region deployment (Render) | — | Not applicable at current scale |
| Access Review | Periodic "who still needs access" review | None automated | ⚠️ Gap — flagged, requires per-org business judgment, not automatable |
| Service Account Lifecycle | Dedicated service-account entity | `APIKey` exists but unused by any auth middleware | ⚠️ Gap — flagged |

## What Step 79 Deliberately Did Not Build

- **Consent management**: this is a B2B operational SaaS with no
  consent-requiring processing (no marketing tracking, no third-party ad
  data sharing) — building a consent system with nothing to consent to
  would be speculative infrastructure.
- **Compliance-in-CI/CD gates**: Step 61 already built the CI/CD pipeline;
  adding automated policy/compliance checks to it is a follow-on, not part
  of this step's scope.
- **A distinct service-account entity type**: `APIKey` already covers the
  real need (a non-human, revocable, expirable credential) — inventing a
  parallel "service account" user type would duplicate it without a clear
  consumer.
- **Data residency controls**: single-region deployment, nothing to control
  yet.

## Governance Review Cadence

Each policy above has a `Review Date` six months out from this step. On
review, check the Compliance Matrix's "Status" column against actual code
state (not just re-reading the policy text) — several rows above have
exact file paths specifically so this check is verifiable, not aspirational.
