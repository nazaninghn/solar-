import os

from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(raw_url: str) -> str:
    """
    27.8: Render's managed Postgres hands out a connection string with
    scheme "postgres://" or "postgresql://" — neither tells SQLAlchemy
    to use this project's driver (psycopg3), so it either falls back to
    a driver that isn't installed or errors outright. Normalized here,
    once, so nothing downstream (session.py, alembic/env.py, tests)
    needs its own copy of this logic.
    """
    if raw_url.startswith("postgresql+"):
        return raw_url

    if raw_url.startswith("postgres://"):
        return "postgresql+psycopg://" + raw_url[len("postgres://"):]

    if raw_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw_url[len("postgresql://"):]

    return raw_url


class Settings:
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "SolarFlow API",
    )

    # 27.38: "development" / "staging" / "production". Kept as the
    # existing APP_ENV name (predates this step) rather than adding a
    # second, differently-named variable that means the same thing.
    APP_ENV: str = os.getenv(
        "APP_ENV",
        "development",
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "false",
    ).lower() == "true"

    # 28.5: "text" (readable in a local terminal) or "json" (structured,
    # for a production log aggregator). Production deploys should set
    # this to "json".
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "text",
    )

    # 28.15: provisional threshold, tunable without a code change.
    SLOW_QUERY_THRESHOLD_MS: int = int(
        os.getenv(
            "SLOW_QUERY_THRESHOLD_MS",
            "1000",
        )
    )

    # 28.37: unset by default — error tracking stays inert until a real
    # Sentry project exists. No account is created by this codebase;
    # this only reads a DSN if one is provided.
    SENTRY_DSN: str = os.getenv(
        "SENTRY_DSN",
        "",
    )

    DATABASE_URL: str = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "",
        )
    )

    # 84: previously unset, so SQLAlchemy's own defaults applied
    # silently (pool_size=5, max_overflow=10, pool_timeout=30,
    # pool_recycle=-1/never). Made explicit and configurable so a real
    # capacity decision under load doesn't require a code change —
    # only tuning these actually changes what CapacityMetric's
    # pool_capacity (app/jobs/finops_jobs.py) measures against, since
    # it reads pool.size()/pool.overflow() from the live engine.
    #
    # The default below (20/30, not SQLAlchemy's 5/10) is not a guess —
    # docs/operations/performance-scalability-report.md's load test
    # measured pool=5/10 producing 6-23% error rates and P95 latency
    # up to 59s at 50-150 concurrent dashboard reads, purely from
    # requests queueing for a connection. Raising to 20/30 eliminated
    # ALL errors and cut P95 by 14-16x at the same load, on this same
    # single Postgres instance. Verify against the actual Render
    # Postgres plan's max_connections before deploying — this default
    # assumes headroom for at least ~30 connections from this service
    # alone, which a Starter-tier-or-above Render Postgres plan has,
    # but a free-tier instance may not.
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT_SECONDS: int = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
    # Postgres (and most managed providers, Render included) can drop a
    # connection that's been idle too long on their side without
    # SQLAlchemy knowing until the next checkout fails; recycling
    # proactively avoids surfacing that as a request-time error.
    DB_POOL_RECYCLE_SECONDS: int = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

    # 27.17: comma-separated list, e.g.
    # "https://app.solarflow.com,https://staging.solarflow.com" — no
    # wildcard default, so a misconfigured production deploy fails
    # closed (no origins allowed) rather than open (every origin
    # allowed).
    CORS_ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]

    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "",
    )

    JWT_ALGORITHM: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "30",
        )
    )

    # 82: general per-IP API rate limit, distinct from the tighter
    # login (5/min) and telemetry (60/min per device) limits — this one
    # is the trust-boundary backstop for every other endpoint, which
    # previously had no limit at all. Generous default so a dashboard
    # doing several concurrent widget fetches doesn't trip it.
    API_RATE_LIMIT_PER_MINUTE: int = int(
        os.getenv(
            "API_RATE_LIMIT_PER_MINUTE",
            "300",
        )
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv(
            "REFRESH_TOKEN_EXPIRE_DAYS",
            "7",
        )
    )

    PASSWORD_RESET_EXPIRE_MINUTES: int = int(
        os.getenv(
            "PASSWORD_RESET_EXPIRE_MINUTES",
            "60",
        )
    )

    EMAIL_VERIFICATION_EXPIRE_HOURS: int = int(
        os.getenv(
            "EMAIL_VERIFICATION_EXPIRE_HOURS",
            "24",
        )
    )

    # 31.22: unset by default — nothing currently stores real device
    # credentials (only SIMULATOR devices exist; Modbus/MQTT are inert
    # stubs), so there's no reason to force every environment to have
    # this configured yet. Required once app.core.encryption is
    # actually used.
    CONNECTION_CONFIG_ENCRYPTION_KEY: str = os.getenv(
        "CONNECTION_CONFIG_ENCRYPTION_KEY",
        "",
    )

    WEATHER_API_KEY: str = os.getenv(
        "WEATHER_API_KEY",
        "",
    )

    # 77.53: synthetic monitoring makes a real outbound HTTP request
    # back to this same process (not an in-process function call) so it
    # catches "not accepting connections" failures an internal check
    # never would. Defaults to the local dev port; Render deployments
    # should set this to the service's own public URL.
    SYNTHETIC_MONITORING_BASE_URL: str = os.getenv(
        "SYNTHETIC_MONITORING_BASE_URL",
        "http://localhost:8000",
    )

    # 78: the Postgres plan's storage ceiling — not enforced by this
    # codebase (Render enforces the actual limit), just the reference
    # point CapacityMetric compares current usage against so "storage
    # at 40% of plan" is a real number instead of an unbounded one.
    # Default matches Render's starter Postgres tier; override per
    # environment via env var once the real plan is known.
    DATABASE_STORAGE_CAPACITY_GB: float = float(
        os.getenv("DATABASE_STORAGE_CAPACITY_GB", "10")
    )

    # Defaults to Open-Meteo (no API key required) so Step 8 is testable
    # without a paid provider account. Swapping providers later only
    # means changing this URL/client, not the rest of the app.
    WEATHER_BASE_URL: str = os.getenv(
        "WEATHER_BASE_URL",
        "https://api.open-meteo.com/v1",
    )


settings = Settings()
