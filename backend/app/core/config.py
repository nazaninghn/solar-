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

    # Defaults to Open-Meteo (no API key required) so Step 8 is testable
    # without a paid provider account. Swapping providers later only
    # means changing this URL/client, not the rest of the app.
    WEATHER_BASE_URL: str = os.getenv(
        "WEATHER_BASE_URL",
        "https://api.open-meteo.com/v1",
    )


settings = Settings()
