# SolarFlow — Version 2 Roadmap (STEP 71)

## V1 Status: Released ✅

v1.0.0 delivered with full energy management, forecasting, optimization, billing, admin, security, monitoring, and documentation.

## V2 Planning Horizons

### NOW (30 Days)
- Connect Frontend to real Backend API (remove mock data)
- Real email provider integration
- Production monitoring tuning (reduce alert noise)
- Critical bug fixes from user feedback

### NEXT (90 Days)
- Real MQTT broker connection (device integration)
- ML-based forecast models (replace baseline)
- Payment provider integration
- Mobile-responsive dashboard improvements
- WebSocket real-time updates

### LATER (6-12 Months)
- Multi-region deployment
- Advanced ML optimization engine
- Mobile app API
- PDF report generation
- Third-party integrations (SCADA, ERP)
- Marketplace / plugin system

## Scalability Targets

| Metric | V1 (Current) | V2 Target |
|--------|-------------|-----------|
| Organizations | 10 | 500 |
| Factories | 50 | 5,000 |
| Devices | 500 | 50,000 |
| Telemetry/sec | 100 | 10,000 |
| Concurrent users | 50 | 2,000 |
| Database size | 1 GB | 100 GB |

## Architecture Evolution

### V1: Modular Monolith ✅
Single FastAPI app with 23 modules. Sufficient for current scale.

### V2: Consider extraction when needed
- Extract telemetry ingestion if volume exceeds single DB capacity
- Extract forecast engine if ML models need GPU/dedicated compute
- Extract notification service if delivery volume is high

**Rule: Don't extract until bottleneck is measured and proven.**

## Key V2 Decisions

| Decision | Options | Criteria |
|----------|---------|----------|
| Real-time | WebSocket vs SSE | Browser support, complexity |
| ML Hosting | In-process vs separate service | Model size, training needs |
| Message Queue | APScheduler vs Celery+Redis | Volume, reliability needs |
| Time-Series DB | PostgreSQL vs TimescaleDB | Telemetry volume |
| Multi-region | Single vs multi | User geography, compliance |

## V2 Non-Goals

- ❌ Rewrite from scratch
- ❌ Switch framework without reason
- ❌ Premature microservices
- ❌ Features without measured demand

## Success Metrics for V2

- P95 latency ≤ 500ms at 10x current load
- 99.9% API availability
- Forecast accuracy MAE < 10%
- User onboarding < 5 minutes
- Cost per organization < €X/month

## Migration Strategy

```
V1 (stable) → V2 features behind flags → Gradual rollout → Full V2
```

No big-bang migration. Each V2 feature ships independently.
