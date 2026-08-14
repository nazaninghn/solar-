# Vendor Governance Policy (STEP 79.41-79.44)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Data Protection | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## Tracked Vendors

Managed via `app/modules/compliance/models.py`'s `Vendor` model and
`/api/v1/compliance/vendors` (SUPER_ADMIN only). Every third party this
platform sends data to or depends on should have a row here.

| Vendor | Purpose | Data Shared | Risk Tier |
|---|---|---|---|
| Open-Meteo Weather API | Solar generation forecasting input | Factory latitude/longitude only — no PII, no customer business data | LOW |
| Render (hosting) | Application hosting, managed Postgres | Everything (infrastructure-level, not a data-sharing relationship) | CRITICAL — not yet added as a formal Vendor row; infrastructure provider risk is inherently platform-wide |

## Risk Tiers (79.42)

| Tier | Definition |
|---|---|
| CRITICAL | Outage or breach would take down the platform or expose customer data at scale (hosting, database provider) |
| HIGH | Handles customer PII or business-sensitive data directly |
| MEDIUM | Handles limited/derived data, or an outage degrades but doesn't break core function |
| LOW | No customer data access, or data shared is already non-sensitive (e.g. geographic coordinates for weather lookup) |

## Vendor Access (79.43)

Each `Vendor.data_access_description` states exactly what the vendor can
see — not a generic "they have API access" note. If a new integration is
added that sends any customer or personal data externally, it must be
recorded here before going live (Privacy by Design, 79.12).

## Vendor Offboarding (79.44)

`POST /api/v1/compliance/vendors/{id}/offboard` moves the governance record
to `OFFBOARDED`. The actual technical steps (revoke API keys, request data
deletion/return, rotate any shared credentials) happen in the vendor's own
systems and are outside what this codebase can automate — this endpoint is
the record that those steps were completed, not the mechanism that performs
them.
