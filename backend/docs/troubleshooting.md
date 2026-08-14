# SolarFlow — Troubleshooting

## Common Issues

### Database Connection Failed
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Fix:**
- Check DATABASE_URL in `.env`
- Ensure PostgreSQL is running
- Verify credentials

### Migration Error: Multiple Heads
```
Multiple head revisions are present
```
**Fix:**
```bash
alembic heads  # See current heads
alembic merge heads -m "merge"  # Merge if needed
```
Or fix `down_revision` in the latest migration.

### 401 Unauthorized
- Token expired → Refresh token
- Token missing → Add `Authorization: Bearer <token>` header
- Token invalid → Re-login

### 403 Forbidden
- User lacks required permission
- Check role in `app/auth/permissions.py`
- Verify resource belongs to user's organization

### 429 Too Many Requests
- Rate limit exceeded
- Wait and retry
- Check quota limits for organization

### 500 Internal Server Error
- Check application logs
- Use `request_id` from response to find in logs
- Check database connectivity
- Check external API status

### Alembic: Target Database Not Up to Date
```bash
alembic upgrade head
```

### Import Error on Startup
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.12+)

## Render Deployment Issues

### Build Fails
- Check `requirements.txt` for invalid packages
- Check Python version compatibility

### Deploy Fails with Migration Error
- Verify DATABASE_URL environment variable
- Check migration chain (single head required)
- Try manual: `alembic upgrade head`

### Health Check Fails
- `/health` should return 200
- `/health/ready` checks database
- If DB is down, readiness fails but liveness passes

## Performance Issues

### Slow Dashboard
- Check if aggregation tables are populated
- Verify database indexes exist
- Check for N+1 queries in logs

### High Memory
- Check for large unbounded queries
- Verify pagination is enforced
- Check worker memory usage
