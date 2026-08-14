# Personal Data Inventory (STEP 79.5-79.6)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Data Protection | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

What personal data this platform actually holds, where, and why. SolarFlow
is B2B — the vast majority of data (factory energy readings, financial
records, device telemetry) belongs to a customer organization, not to any
individual person. This inventory covers the minority of fields that are
genuinely personal data.

## Identity & Contact

| Data | Table.Column | Purpose | Retention |
|---|---|---|---|
| Full name | `users.full_name` | Display name, audit attribution | Until account deletion (see [retention-policy.md](retention-policy.md)) |
| Email | `users.email` | Login identifier, notifications | Until account deletion |

## Account & Authentication

| Data | Table.Column | Purpose | Retention |
|---|---|---|---|
| Password hash (Argon2, never plaintext) | `users.hashed_password` | Login | Until account deletion |
| Role | `users.role` | Access control | Until account deletion |
| Verification/activity flags | `users.is_active`, `users.is_verified`, `users.last_login_at` | Account state | Until account deletion |
| Refresh tokens (SHA-256 hash, never raw) | `refresh_tokens.token_hash` | Session management | Revoked on logout/rotation |

## Usage & Security

| Data | Table.Column | Purpose | Retention |
|---|---|---|---|
| Admin/user actions | `audit_logs`, `admin_audit_logs` | Accountability, compliance evidence | Indefinite (audit trail — deliberately excluded from automated purge, see retention-policy.md) |
| Security events (login attempts, IP, user agent) | `security_events` | Brute-force detection, incident investigation | Indefinite (same reasoning as above) |
| Recommendation accept/reject decisions | `recommendation_audit_logs` | Accountability for automated-decision review | Indefinite |

## What is explicitly NOT collected

- No payment card data (billing is invoice-based, no card numbers ever touch this backend)
- No biometric, health, or special-category data
- No location tracking of individual people — `factories.latitude`/`longitude` is industrial site location, not a person's location
- No behavioral/marketing tracking, no cookies beyond session auth

## Data Minimization (79.7)

Every personal field above is collected because a specific, named feature
depends on it (login needs email+password, audit needs an actor,
notifications need an address). There is no field collected "in case it's
useful later."

## Self-Service Rights (79.36-79.40)

Implemented at `GET /api/v1/auth/me/export` (full JSON export of everything
in this inventory tied to the requesting user) and `POST /api/v1/auth/me/delete`
(anonymizes the account — see `app/modules/auth/data_rights.py` for exactly
what does and doesn't get scrubbed, and why audit trail rows are preserved
with an anonymized `user_id` reference rather than deleted).
