# SolarFlow — Security Hardening Checklist (STEP 53)

## Transport Security
- [x] HTTPS enforced in production (Render handles TLS)
- [x] HSTS header sent when behind HTTPS proxy
- [x] No sensitive data transmitted over HTTP

## CORS
- [x] CORS origins restricted to known frontend domains
- [x] No wildcard `*` in production CORS config

## Authentication
- [x] All private endpoints require authentication
- [x] JWT with short-lived access tokens
- [x] Refresh token rotation
- [x] Token revocation on logout
- [x] Password hashing with Argon2id
- [x] Account lockout after failed attempts

## Authorization
- [x] RBAC with granular permissions
- [x] Server-side enforcement (not just UI)
- [x] Object-level authorization (IDOR protection)
- [x] Tenant isolation (organization_id scoping)
- [x] Admin endpoints require platform admin role

## Input Validation
- [x] Pydantic schema validation on all endpoints
- [x] Request body size limits
- [x] Path traversal protection
- [x] SQL injection protected (SQLAlchemy ORM)
- [x] Mass assignment guard (protected fields)
- [x] File upload validation (extension, size, name)

## Rate Limiting
- [x] Login rate limiting (5/min per IP+email, `app/auth/rate_limit.py`)
- [x] General API rate limiting (300/min per IP, `app/core/api_rate_limit.py`, Step 82) — per-IP, not per-user/org; corrected from this checklist's earlier claim
- [x] Brute force protection with lockout (`app/modules/security/lockout.py`, Step 47) — **wired into the actual login flow in Step 86**; the module existed fully implemented since Step 47 but had no caller anywhere until this step, so this box was previously checked incorrectly

## Secrets Management
- [x] Secrets in environment variables only
- [x] No secrets in git repository
- [x] .env in .gitignore
- [x] API keys stored as SHA-256 hash
- [x] Device credentials encrypted

## Token Security
- [x] Access token expiration configured
- [x] Refresh token rotation
- [x] JWT algorithm specified (not "none")
- [x] Token payload minimal (no sensitive data)

## Error Handling
- [x] No stack traces in production responses
- [x] Standard error format with error codes
- [x] Generic auth error messages (no enumeration)
- [x] Request ID in all error responses

## Logging & Audit
- [x] Security events logged (login, role change, etc.)
- [x] Audit logs are append-only
- [x] No passwords/tokens in logs
- [x] Structured logging with correlation IDs
- [x] Sensitive data redacted from logs

## Data Protection
- [x] Database connection over TLS
- [x] PII minimized
- [x] Backup encryption

## SSRF Protection
- [x] URL validation for external fetches
- [x] Private IP ranges blocked
- [x] Metadata endpoint blocked

## Dependencies
- [x] requirements.txt with pinned versions
- [x] No known critical vulnerabilities (audit regularly)

## Admin Security
- [x] Platform admin role enforcement
- [x] Admin actions audited
- [x] Feature flags for dangerous features
- [x] Maintenance mode available

## Production Config
- [x] APP_ENV=production
- [x] DEBUG=false
- [x] Unique JWT_SECRET (not dev value)
- [x] CORS limited to production frontend
- [x] Health checks configured
