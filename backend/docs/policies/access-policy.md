# Access Control Policy (STEP 79.16-79.21)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Data Protection | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## Role Model

Six roles (`app/models/user.py`'s `USER_ROLES`), enforced by a permission
matrix (`app/auth/permissions.py`'s `ROLE_PERMISSIONS`) rather than
hardcoded role checks scattered through the codebase:

| Role | Scope |
|---|---|
| `SUPER_ADMIN` | Platform-wide — every organization, every endpoint under `/api/v1/admin` and `/api/v1/compliance` |
| `COMPANY_ADMIN` | Full access within their own organization only |
| `FACTORY_MANAGER` | Manage energy/battery/factory settings for assigned factories |
| `ENERGY_MANAGER` | Manage energy/battery/recommendations for assigned factories |
| `FINANCIAL_MANAGER` | View-only + manage financial data for assigned factories |
| `VIEWER` | Read-only |

## Least Privilege (79.17)

Every mutating endpoint requires an explicit permission via
`require_permission()` — there is no default-allow path. Platform-wide
admin endpoints (`_require_platform_admin` in `app/modules/admin/router.py`
and `_require_super_admin` in `app/modules/compliance/router.py`) require
`SUPER_ADMIN` specifically, not `COMPANY_ADMIN` — a company's own admin
manages their own organization through `/api/v1/company/*`, never through
the platform-wide surface.

**Note:** `_require_platform_admin` previously accepted `COMPANY_ADMIN`,
letting any company's admin list and modify every other company's
organizations and users. Fixed as part of Step 79 (see
`app/modules/admin/router.py` — this was a real cross-tenant privilege
escalation, not an intentional scoping choice, caught while implementing
the tenant-isolation test suite).

## Privileged Access (79.18)

Distinct, separately-controlled surfaces:

| Surface | Gate |
|---|---|
| Admin panel (`/api/v1/admin/*`) | `SUPER_ADMIN` |
| Compliance & governance (`/api/v1/compliance/*`) | `SUPER_ADMIN` |
| Production monitoring (`/api/v1/admin/monitoring/*`) | `SUPER_ADMIN` or `COMPANY_ADMIN` (platform-health visibility, not data mutation) |
| Security events (`/api/v1/admin/security/*`) | Same as monitoring |
| Factory-scoped data | `get_accessible_factory` — organization boundary (404 for cross-org) + `UserFactoryAccess` scoping (403 for same-org-but-unassigned) |

## Offboarding (79.20)

`deactivate_company_user` (`app/modules/company/service.py`): sets
`is_active=False` and revokes every active refresh token immediately. Not a
hard delete — audit trail integrity is preserved (see retention-policy.md).
A user can also self-service this via `POST /api/v1/auth/me/delete`, which
additionally anonymizes their PII (see personal-data-inventory.md).

## Access Review (79.19)

No automated periodic access review job exists. This is a genuine gap —
flagged, not built, since "who should still have access" is a business
judgment call for each organization's admin to make on a cadence they
choose, not something this codebase can decide unilaterally. `UserFactoryAccess`
rows are queryable per-factory for a manual review today.

## Service Accounts (79.21)

No distinct "service account" entity exists. `APIKey` (`app/modules/admin/models.py`)
is the closest equivalent — organization-scoped, revocable, with
`last_used_at`/`expires_at` tracking — but as of this step it is not yet
consumed by any authentication middleware (see Step 79 DoD recap for the
full note on this gap).
