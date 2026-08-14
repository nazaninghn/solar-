# Data Retention Policy (STEP 79.31-79.35)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Data Protection | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## Retention by Data Type

| Data Type | Retention | Reason | Enforcement |
|---|---|---|---|
| Raw device telemetry (`device_energy_readings`) | 90 days | High-volume (polling-cadence), superseded by hourly/daily/monthly aggregates | `app.jobs.retention_jobs.purge_old_telemetry`, cron 02:30 |
| System metric snapshots (`system_metric_snapshots`) | 30 days | Operational trend data, no long-term value | `app.jobs.retention_jobs.purge_old_observability_data`, cron 02:45 |
| Data quality events (`data_quality_events`) | 180 days | Event log, not a compliance record | Same job |
| Energy aggregates (hourly/daily/monthly) | Indefinite | Low volume, business-relevant history (year-over-year reporting) | Not purged |
| Audit trails (`audit_logs`, `admin_audit_logs`, `recommendation_audit_logs`) | Indefinite | Compliance/accountability record — see below | Not purged |
| Security events (`security_events`) | Indefinite | Incident investigation, brute-force pattern history | Not purged |
| User account data | Until self-deletion or admin deactivation | See [personal-data-inventory.md](personal-data-inventory.md) | `POST /api/v1/auth/me/delete` (self-service), `deactivate_company_user` (admin) |

## Why audit trails are excluded from automatic purge

This was a deliberate decision (see comments in `app/jobs/retention_jobs.py`),
not an oversight: audit trails are exactly the kind of record a customer may
have their own regulatory or contractual reason to keep — picking a
retention window for someone else's compliance obligation isn't a call an
automated job should make. If a customer needs audit log retention limits,
that's a policy configuration to add per-organization, not a global default.

## Legal Hold (79.33)

`app/modules/compliance/models.py`'s `LegalHold` suspends both automated
retention purges (`app/jobs/retention_jobs.py` excludes any factory
belonging to a held organization) and self-service account deletion
(`app/modules/auth/data_rights.py`) for the duration of the hold. Managed via
`POST /api/v1/compliance/legal-holds` (SUPER_ADMIN only).

## Backup Retention (79.35)

Backup lifecycle is tracked in `backup_records` (`app/modules/security/models.py`,
Step 47) — `expires_at` per backup, `BackupRecord.status`. Backups are managed
by the hosting platform's own backup rotation; this table records what
exists and when it expires, it does not itself perform deletion.

## Secure Deletion (79.34)

All deletion in this codebase is a standard SQL `DELETE` against managed
Postgres storage (Render) — there is no local/on-prem disk to wipe, so
DoD-5220-style overwrite procedures don't apply. The database provider's own
storage-layer deletion guarantees apply.
