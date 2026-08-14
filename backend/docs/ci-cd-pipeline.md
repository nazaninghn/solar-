# SolarFlow — CI/CD Pipeline & Quality Gate (STEP 61)

## Pipeline Overview

```
Developer → Push → CI → Quality Gate → Staging → Production
```

## GitHub Actions Pipeline

```yaml
# .github/workflows/ci.yml (conceptual — adapt to actual setup)

name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    - Checkout code
    - Install dependencies
    - Run linter (ruff/flake8)
    - Run formatter check

  test:
    - Checkout code
    - Install dependencies
    - Setup test database
    - Run unit tests
    - Run integration tests
    - Upload coverage report

  security:
    - Dependency vulnerability scan
    - Secret detection scan
    - SAST (static analysis)

  build:
    - Verify application starts
    - Verify migrations apply cleanly
    - Verify health check responds

  deploy-staging:
    needs: [lint, test, security, build]
    - Deploy to staging
    - Run smoke tests
    - Run E2E tests

  deploy-production:
    needs: [deploy-staging]
    if: github.ref == 'refs/heads/main'
    - Deploy to Render (auto-deploy)
    - Run production smoke tests
    - Monitor error rate
```

## Quality Gate — Must Pass Before Merge

| Check | Tool | Threshold |
|-------|------|-----------|
| Lint | ruff | 0 errors |
| Type check | mypy (optional) | 0 errors |
| Unit tests | pytest | 100% pass |
| Integration tests | pytest | 100% pass |
| Coverage | pytest-cov | > 70% critical paths |
| Security scan | safety/pip-audit | No critical/high |
| Secret scan | detect-secrets | 0 secrets |
| Build | uvicorn start test | Healthy |

## Test Strategy

### Test Pyramid
```
        E2E (5-10)
       /          \
    Integration (30-50)
   /                    \
  Unit Tests (100-200)
```

### What MUST Be Tested
- Authentication (login, token, refresh, logout)
- Authorization (RBAC, permissions)
- Tenant isolation (cross-org access blocked)
- Input validation (boundary, negative)
- Financial calculations (billing, settlements)
- Energy calculations (KPIs, aggregation)
- Security (IDOR, injection, rate limit)

### Test Database
- Separate PostgreSQL for tests
- Fresh migrations per test run
- Transaction rollback per test (isolation)
- No production data ever

## Branch Protection

### `main` branch rules:
- [ ] Require pull request before merge
- [ ] Require status checks to pass (CI)
- [ ] Require at least 1 approval
- [ ] No direct push
- [ ] No force push

## PR Requirements

Every PR must have:
1. Description of changes
2. All CI checks passing
3. No security warnings
4. Tests for new code
5. Documentation updated (if API change)

## Deployment Flow

```
PR Merged to main
    ↓
CI runs (lint + test + security)
    ↓ All pass?
Render auto-deploys
    ↓
alembic upgrade head (migrations)
    ↓
uvicorn starts
    ↓
Health check passes
    ↓
LIVE
```

## Rollback

If deployment fails:
1. Render shows failed deploy → previous version stays active
2. If health check fails → Render auto-reverts
3. Manual rollback: Render dashboard → select previous deploy → redeploy

## Monitoring After Deploy

First 30 minutes after deploy, watch:
- Error rate (should not spike)
- Latency (should not increase significantly)
- Health checks (must stay green)
- Queue processing (workers alive)

## Running Tests Locally

```bash
# All tests
pytest

# Unit tests only
pytest tests/ -m "not integration"

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/integration/test_auth.py -v
```

## Adding New Tests

When you add a feature:
1. Write unit test for business logic
2. Write integration test for API endpoint
3. Add negative/boundary cases
4. If security-sensitive: add security test
5. If user-facing: consider E2E test

## Flaky Test Policy

- Flaky test found → Immediately investigate
- Don't ignore/skip without tracking
- Fix within 48 hours or quarantine with ticket
- Never let flaky tests erode CI trust
