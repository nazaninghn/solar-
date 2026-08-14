# Zero-Trust Security Architecture (STEP 82)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## The Honest Starting Point

Nothing in this codebase was ever named "zero-trust" before this document,
but the authentication model has been zero-trust-shaped since Step 24: JWT
access tokens with no server-side session store, verified fresh against the
database on every single request. There was never a "log in once, trust the
cookie for the next eight hours" path to retrofit away from. Step 82's real
work was closing three concrete gaps — an audit trail that was built but
never written to, a rate limit that only covered two of dozens of endpoint
groups, and a service-identity credential that was issuable but not
checkable — not re-architecting authentication.

## Pillar 1: Identity-Based Access — already real

Every request carries a JWT (`app/core/security.py`); there is no session
cookie anywhere in this codebase. `get_current_user`
(`app/core/dependencies.py`) decodes it and re-fetches the user from the
database on every call — not from a cache, not from the token payload alone.
A deactivated user (`User.is_active = False`) is rejected on their very next
request, not at next login.

## Pillar 2: Least Privilege — already real

Six roles, a single permission matrix (`app/auth/permissions.py`'s
`ROLE_PERMISSIONS`), enforced via `require_permission()` on every mutating
endpoint — no endpoint defaults to allow. Documented in full in
`docs/policies/access-policy.md` (Step 79); not duplicated here.

## Pillar 3: Continuous Verification — already real

There is no "trust for the rest of this session" concept anywhere in this
codebase. `get_current_user` queries the database on every request; a
revoked refresh token, a deactivated user, or an expired access token is
caught on the very next call, not at the next login. This is what "never
trust, always verify" concretely means for a stateless JWT API — it was
already true before Step 82, not something this step introduced.

## Pillar 4: Privileged Access — already real

Platform-wide operations (`/api/v1/admin`, `/api/v1/compliance`,
`/api/v1/finops`, `/api/v1/bi`, `/api/v1/ai-readiness`) require
`SUPER_ADMIN` specifically — fixed for `/api/v1/admin` in Step 79 after a
cross-tenant escalation was found there. Operational control actions
(emergency stop, device commands) require `MANAGE_ENERGY`, which is the
correct, narrower gate for an operational action versus a platform-governance
one — conflating the two would either lock operators out of legitimate
emergency actions or hand platform governance to every factory manager.

## Pillar 5: Security Monitoring — real gap, closed in Step 82

`SecurityEvent` (Step 47/53) and its correlation job
(`app/modules/security/correlation.py`, Step 79) existed, but
`log_security_event()` had never actually been called anywhere — the audit
trail was schema without data, and the correlation job had nothing to
correlate. Step 82 wires it into the paths that actually matter:

| Event | Where | Severity |
|---|---|---|
| `LOGIN_SUCCESS` / `LOGIN_FAILED` | `app/modules/auth/router.py`'s `/login` | INFO |
| `TOKEN_REUSE` | `app/modules/auth/service.py`'s `refresh_access_token` — specifically when an *already-rotated* refresh token is presented again, not a merely-expired one | HIGH |
| `PERMISSION_DENIED` | `app/auth/dependencies.py`'s `require_permission` | INFO |
| `SUSPICIOUS_REQUEST` | `app/devices/auth.py` (invalid/revoked device key, or a valid key used against the wrong device_id) and `app/modules/admin/api_key_auth.py` (invalid/revoked/expired API key) | INFO / HIGH |
| `RATE_LIMIT_EXCEEDED` | `app/core/api_rate_limit.py` | INFO |

The existing correlation job (runs every 5 minutes) now has real signal to
work with: 3+ `LOGIN_FAILED` from one IP in 15 minutes still opens a
brute-force incident, and `PERMISSION_DENIED` clusters still feed the
privilege-escalation-pattern check — both checks existed since Step 79, they
were just never exercised.

## Pillar 6: Service Identity — real gap, closed in Step 82

Two non-user credential types exist:

- **Device keys** (`Device.device_key_hash`, Step 26) — already fully
  wired: hashed, checked on every telemetry request, revocable via
  `is_active`. Step 82 only added the missing audit logging around it.
- **Organization API keys** (`APIKey`, Step 46) — created and revoked via
  the admin panel since Step 46, but *nothing in the entire codebase ever
  checked one*. `app/modules/admin/api_key_auth.py`'s
  `get_organization_from_api_key` now does: hash the presented `X-API-Key`
  header, look it up, reject if revoked/expired, stamp `last_used_at`.
  Applied to exactly one new endpoint,
  `GET /api/v1/integrations/energy-summary`
  (`app/modules/admin/integrations_router.py`) — deliberately read-only and
  minimal, since an API key has no role of its own to gate a wider surface
  with the way a user JWT does. Expand only when a real external-integration
  need shows up, not speculatively.

## Pillar 7: Rate Limiting / Abuse Protection — partial gap, closed in Step 82

Login (`app/auth/rate_limit.py`, 5/min per IP+email) and device telemetry
(`app/devices/rate_limit.py`, 60/min per device) were already rate-limited.
Every other endpoint — every dashboard query, every factory list, every
report — had no limit at all. `app/core/api_rate_limit.py`'s
`GeneralAPIRateLimitMiddleware` closes this: 300 requests/minute per IP
(`API_RATE_LIMIT_PER_MINUTE`, configurable), applied as the outermost
middleware so an abusive caller is rejected before CORS handling, request
logging, or a database session — exempting only `/health` and
`/health/ready`, which Render polls on a fixed interval independent of real
traffic.

Same in-memory, single-instance caveat as the other two rate limiters
(documented at each definition) — would need a shared store if this ever
runs as more than one process behind a load balancer.

## Pillar 8: CORS / Origin Trust — already real

`CORS_ALLOWED_ORIGINS` fails closed: an unset env var means zero origins are
allowed, not a wildcard. No hardcoded origin list exists anywhere.

## Pillar 9: Network / Micro-Segmentation — not applicable, documented

**N/A, by architecture, not by omission.** SolarFlow runs as a single Render
web service against a single managed Postgres instance — no VPC, no
subnets, no service mesh, no containers to place network policy between.
There is exactly one network boundary that matters: Render's own
HTTPS-terminated edge, which every request already crosses. Segmenting
traffic *within* a single process is not a meaningful security control; it
would be organizational theater. If this ever becomes a genuine multi-service
deployment (a separate worker fleet, a separate internal API), this section
needs a real rewrite — not before.

## Summary

| Pillar | Status |
|---|---|
| Identity-based access | Already real (Step 24) |
| Least privilege | Already real (Step 24, documented Step 79) |
| Continuous verification | Already real (Step 24) |
| Privileged access separation | Already real (Step 79) |
| Security monitoring | Gap closed — `log_security_event` now actually called |
| Service identity (devices) | Already real (Step 26); audit logging added |
| Service identity (API keys) | Gap closed — `APIKey` now actually consumed |
| Rate limiting | Gap partially closed — general 300/min/IP backstop added |
| CORS / origin trust | Already real (Step 27) |
| Network segmentation | N/A — single-service architecture, documented |
