# SolarFlow — Architecture

## System Overview

```
┌─────────────────┐
│    Frontend     │  Next.js + TypeScript + TailwindCSS
│   (Vercel)      │
└────────┬────────┘
         │ HTTPS
┌────────▼────────┐
│   Backend API   │  FastAPI + Python 3.12
│   (Render)      │
└────────┬────────┘
    ┌────┼────────────────┐
    │    │                │
┌───▼──┐ ┌──▼───┐  ┌─────▼─────┐
│  DB  │ │Queue │  │ External  │
│(PG)  │ │(Jobs)│  │   APIs    │
└──────┘ └──┬───┘  └───────────┘
            │         Weather
      ┌─────▼─────┐   Price
      │  Workers  │   Payment
      └───────────┘   Email
```

## Backend Modules

| Module | Purpose |
|--------|---------|
| auth | Authentication, JWT, MFA |
| company | Organization management |
| factories | Factory CRUD |
| devices | Device registry |
| energy | Energy readings |
| battery | Battery management |
| weather | Weather data |
| forecast | Energy forecasting |
| pricing | Electricity prices |
| recommendations | AI recommendations |
| financial | Financial records |
| notifications | User notifications |
| analytics | Energy analytics |
| control | Energy actions (Step 32) |
| gateway | Device adapters (Step 33) |
| pipeline | Data pipeline (Step 34) |
| forecasting | Forecast engine (Step 35) |
| optimization | Smart recommendations (Step 36) |
| finance | Financial engine (Step 37) |
| orchestrator | Command orchestration (Step 38) |
| iot_gateway | MQTT/IoT (Step 39) |
| alerts | Alert system (Step 40) |
| observability | Data quality (Step 41) |
| events | Events & notifications (Step 43) |
| billing | Billing & settlement (Step 44) |
| advanced_analytics | KPIs & anomalies (Step 45) |
| admin | Admin panel (Step 46) |
| security | Security hardening (Step 47/53) |
| monitoring | Production monitoring (Step 49) |
| data_integrity | Reconciliation (Step 50) |
| performance | Scalability (Step 51) |
| disaster_recovery | DR & backup (Step 52) |
| testing | Smoke tests (Step 48) |

## Data Flow

```
Device → MQTT → Gateway → Validation → Normalization → Storage
                                                         │
                                          ┌──────────────┼──────────────┐
                                          ▼              ▼              ▼
                                     Aggregation    Forecasting    Real-time
                                          │              │              │
                                          ▼              ▼              ▼
                                        KPIs      Recommendations   Alerts
                                          │              │              │
                                          └──────────────┼──────────────┘
                                                         ▼
                                                     Dashboard
```

## Database

- PostgreSQL 16 (Render managed)
- ~97 tables across all modules
- Alembic for migrations
- Multi-tenant (organization_id scoping)

## Authentication

- JWT (Access + Refresh tokens)
- Argon2id password hashing
- Account lockout (brute force protection)
- RBAC with granular permissions

## Deployment

- Render Web Service (Python)
- Auto-deploy from `main` branch
- Health check: `/health`
- Start: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
