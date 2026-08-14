# SolarFlow — Developer Onboarding

Welcome! Follow these steps to get started.

## Day 1: Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nazaninghn/solar-.git
   cd solar-/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local PostgreSQL connection string.

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

7. **Verify it works**
   - Open http://localhost:8001 → Should see API info
   - Open http://localhost:8001/docs → Swagger UI

## Day 1: Explore

- Browse `/docs` to see all API endpoints
- Read `docs/architecture.md` for system overview
- Read `docs/setup.md` for detailed setup

## Day 2: Understand the Code

Key files to read:
- `app/main.py` — App initialization, middleware, routers
- `app/core/config.py` — Configuration
- `app/auth/permissions.py` — RBAC system
- `app/modules/` — Feature modules (pick one to explore)

## Day 3: Make Your First Change

1. Create a branch: `git checkout -b feature/my-first-change`
2. Add a simple endpoint or fix a small issue
3. Write a test for it
4. Run tests: `pytest`
5. Submit a PR

## Key Concepts

- **Multi-tenant**: All data is scoped by `organization_id`
- **RBAC**: Permissions checked server-side (not just UI)
- **Modules**: Each feature is self-contained in `app/modules/`
- **Migrations**: Database changes through Alembic only
- **Single alembic head**: Never create branching migrations

## Getting Help

- Check `docs/troubleshooting.md` for common issues
- Check Swagger `/docs` for API reference
- Review existing modules for code patterns
