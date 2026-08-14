# SolarFlow API Contract

## Base URL
- Production: `https://solarflow-api.onrender.com`
- Development: `http://localhost:8001`

## Authentication
All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

## Response Format

### Success
```json
{
  "data": { ... },
  "meta": { "page": 1, "limit": 25, "total": 100 }
}
```

### Error
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

## Error Codes
| Code | Description |
|------|-------------|
| AUTH_INVALID_CREDENTIALS | Wrong email/password |
| AUTH_TOKEN_EXPIRED | Access token expired |
| FORBIDDEN | Insufficient permissions |
| RESOURCE_NOT_FOUND | Item does not exist |
| RATE_LIMITED | Too many requests |
| VALIDATION_FAILED | Invalid request body |
| DEVICE_OFFLINE | Device not reachable |
| PAYMENT_FAILED | Payment processing error |
| INTERNAL_ERROR | Unexpected server error |

## API Versioning
All endpoints are versioned: `/api/v1/...`

## Pagination
List endpoints support:
- `?page=1&limit=25` (default limit: 25, max: 200)
- `?sort=created_at` or `?sort=-created_at` (descending)

## Filtering
Common filters:
- `?status=ACTIVE`
- `?date_from=2026-01-01&date_to=2026-12-31`
- `?factory_id=1`
- `?search=keyword`

---

## Core Endpoints

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Liveness check |
| GET | `/health/ready` | No | Readiness (DB check) |

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/refresh` | No | Refresh token |
| POST | `/api/v1/auth/logout` | Yes | Logout |
| GET | `/api/v1/auth/me` | Yes | Current user |

### Factories
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/factories` | Yes | List factories |
| POST | `/api/v1/factories` | Yes | Create factory |
| GET | `/api/v1/factories/{id}` | Yes | Get factory |

### Devices
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/factories/{id}/devices` | Yes | List devices |
| POST | `/api/v1/factories/{id}/devices` | Yes | Create device |

### Analytics
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/factories/{id}/analytics/overview` | Yes | Analytics overview |
| GET | `/api/v1/factories/{id}/analytics/kpis` | Yes | Energy KPIs |
| GET | `/api/v1/factories/{id}/forecast` | Yes | Forecast summary |

### Billing
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/billing/plans` | No | List plans |
| GET | `/api/v1/billing/subscription` | Yes | Current subscription |
| GET | `/api/v1/billing/invoices` | Yes | List invoices |

### Admin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/admin/dashboard` | Admin | Platform KPIs |
| GET | `/api/v1/admin/health` | Admin | System health |
