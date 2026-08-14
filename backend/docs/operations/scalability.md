# SolarFlow — Performance & Scalability Guide (STEP 58)

## Current Architecture

```
Client → API (Render) → PostgreSQL (Render)
                     → Queue (Background Jobs)
                     → Workers
                     → External APIs
```

## Performance Targets

| Endpoint | P95 Target | Max Error Rate |
|----------|-----------|----------------|
| Login | < 300ms | < 0.5% |
| Dashboard | < 500ms | < 1% |
| Device List | < 400ms | < 1% |
| Analytics | < 800ms | < 1% |
| Telemetry Ingest | < 200ms | < 0.5% |
| Reports | Async | N/A (queued) |

## Database Optimization

### Index Strategy
Key indexes for common queries:
- `factory_id + created_at` (device lookups)
- `organization_id` (tenant scoping)
- `device_id + timestamp` (telemetry)
- `status` (active record filtering)

### N+1 Prevention
- Use eager loading / joined queries for related data
- Batch queries when loading lists with relations
- Never query inside a loop

### Query Rules
- All list endpoints must have `LIMIT`
- No `SELECT *` in production queries
- Use cursor pagination for large datasets (telemetry)

## Caching Strategy

### What to Cache
- Organization/factory metadata (changes rarely)
- Dashboard KPIs (TTL: 60s)
- Forecast results (TTL: 5min)
- System config (TTL: 5min)

### What NOT to Cache
- Authentication decisions
- Financial calculations
- Real-time telemetry
- Anything security-sensitive

### Invalidation
- On data write → invalidate related cache
- On deploy → flush all cache
- TTL as safety net (never rely solely on invalidation)

## Async Processing

### Move to Queue
- Report generation
- Large analytics computation
- Data reprocessing
- Bulk exports
- Email/notification delivery
- Forecast generation

### Keep Synchronous
- Login/auth
- Simple CRUD
- Health checks
- Small reads

## Telemetry at Scale

### Ingestion Path
```
Device → API → Validation → Queue → Worker → DB
```

### Optimization
- Batch inserts (group multiple readings)
- Pre-aggregation (5min → hourly → daily)
- Partition large tables by time
- Archive old raw data (keep aggregates)

### Retention Policy
| Data Type | Retention |
|-----------|-----------|
| Raw telemetry | 90 days |
| 5-min aggregates | 1 year |
| Hourly aggregates | 2 years |
| Daily summaries | 5 years |
| Financial records | 7 years |

## Horizontal Scaling Readiness

### Stateless API ✅
- JWT-based auth (no server sessions)
- No in-memory state between requests
- Database/Redis for shared state

### Multi-Instance Ready
- Connection pool per instance
- Queue workers can run in parallel
- No file-system dependencies

### Scaling Triggers
| Metric | Action |
|--------|--------|
| CPU > 70% sustained | Scale out |
| P95 > 2x target | Investigate + scale |
| Queue depth > 500 | Add workers |
| DB connections > 80% | Optimize or scale DB |

## Circuit Breaker

External services protected:
- Weather API: 5 failures → OPEN → 60s recovery
- Payment provider: 3 failures → OPEN → 30s recovery
- Email service: 5 failures → OPEN → 120s recovery

## Load Testing Scenarios

### Normal Load
- 100 concurrent users
- Mixed read/write operations
- Expected: all targets met

### Peak Load
- 500 concurrent users
- Heavy analytics + telemetry
- Expected: P95 < 2x normal

### Stress Test
- Increase until failure
- Find breaking point
- Document capacity ceiling

### Soak Test
- 200 users for 4+ hours
- Check for memory leaks
- Check for connection leaks
- Check queue growth

## Resource Limits

| Resource | Limit | Action on Exceed |
|----------|-------|------------------|
| Request body | 10MB | 413 |
| Page size | 200 | Cap at max |
| API rate | Per plan | 429 |
| Telemetry rate | Per plan | 429 |
| Export size | 100K rows | Queue + download |

## Graceful Degradation

If a non-critical service fails:
- Weather API down → Dashboard shows "Weather unavailable"
- Analytics slow → Show cached data with "updating" indicator
- Forecast failed → Show last valid forecast

Core services (auth, CRUD, telemetry ingest) must remain available.
