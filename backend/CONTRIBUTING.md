# Contributing to SolarFlow

## Branch Strategy

```
main          — Production (auto-deploys to Render)
feature/*     — New features
fix/*         — Bug fixes
hotfix/*      — Critical production fixes
```

## Commit Convention

```
feat: add device analytics endpoint
fix: resolve tenant isolation issue
refactor: simplify forecast engine
docs: update API documentation
test: add billing integration tests
chore: update dependencies
security: fix IDOR vulnerability
```

## Pull Request Process

1. Create a branch from `main`
2. Make your changes
3. Write/update tests
4. Update documentation if needed
5. Ensure all tests pass: `pytest`
6. Submit PR with description

## PR Template

```markdown
## What changed?
Brief description of changes.

## Why?
Context and motivation.

## Tests
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing done

## Breaking Changes
None / List any breaking changes

## Security Impact
None / Describe security implications

## Checklist
- [ ] Code follows project patterns
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] Migration included (if DB change)
```

## Code Review Checklist

- [ ] Logic correct
- [ ] Security: auth, validation, tenant isolation
- [ ] Tests cover happy + error paths
- [ ] No N+1 queries
- [ ] Proper error handling
- [ ] Logging appropriate (no secrets)
- [ ] Documentation updated

## Key Rules

1. **Never commit secrets** to git
2. **Always scope queries** by organization_id
3. **Always validate** inputs server-side
4. **Always write tests** for new endpoints
5. **Single alembic head** — no migration branches
6. **Use existing patterns** — look at similar modules
