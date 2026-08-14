# SolarFlow Backend — Setup Guide

## Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Git

## Quick Start

```bash
# Clone
git clone https://github.com/nazaninghn/solar-.git
cd solar-/backend

# Virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your DATABASE_URL and JWT_SECRET

# Database migrations
alembic upgrade head

# Run
uvicorn app.main:app --reload --port 8001
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET` | Secret for JWT signing | Yes |
| `APP_ENV` | Environment (development/production) | Yes |
| `DEBUG` | Enable debug mode (true/false) | No |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend URLs | Production |
| `WEATHER_BASE_URL` | Weather API base URL | No |

## Database

```bash
# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_auth.py

# Run with coverage
pytest --cov=app
```

## API Documentation

After starting the server:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- OpenAPI JSON: http://localhost:8001/openapi.json

## Health Checks

- Liveness: `GET /health`
- Readiness: `GET /health/ready`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app + middleware
│   ├── core/                # Config, security, deps
│   ├── auth/                # Auth utilities
│   ├── database/            # SQLAlchemy session
│   ├── models/              # SQLAlchemy models
│   ├── modules/             # Feature modules
│   │   ├── auth/
│   │   ├── factories/
│   │   ├── devices/
│   │   ├── control/
│   │   ├── gateway/
│   │   ├── pipeline/
│   │   ├── forecasting/
│   │   ├── optimization/
│   │   ├── finance/
│   │   ├── billing/
│   │   ├── alerts/
│   │   ├── admin/
│   │   ├── security/
│   │   └── ...
│   └── jobs/                # Background jobs
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docs/                    # Documentation
├── requirements.txt
├── .env.example
└── README.md
```
