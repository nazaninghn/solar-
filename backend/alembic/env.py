from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.database.base import Base
from app import models  # noqa: F401 - importing the package registers every model with Base.metadata

# STEP 33-52's modules each define their own models.py but were never
# imported anywhere env.py's import chain reaches — Base.metadata
# didn't know they existed, so `alembic revision --autogenerate` saw
# ~90 "extra" tables in the live database it didn't recognize and
# proposed dropping every one of them. Importing each module here
# (same "import registers with Base.metadata" mechanism as the `app
# import models` line above) fixes autogenerate without changing any
# actual schema.
from app.modules.admin import models as _admin_models  # noqa: F401
from app.modules.advanced_analytics import models as _advanced_analytics_models  # noqa: F401
from app.modules.alerts import models as _alerts_models  # noqa: F401
from app.modules.billing import models as _billing_models  # noqa: F401
from app.modules.compliance import models as _compliance_models  # noqa: F401
from app.modules.control import models as _control_models  # noqa: F401
from app.modules.data_integrity import models as _data_integrity_models  # noqa: F401
from app.modules.disaster_recovery import models as _disaster_recovery_models  # noqa: F401
from app.modules.events import models as _events_models  # noqa: F401
from app.modules.finance import models as _finance_models  # noqa: F401
from app.modules.forecasting import models as _forecasting_models  # noqa: F401
from app.modules.gateway import models as _gateway_models  # noqa: F401
from app.modules.iot_gateway import models as _iot_gateway_models  # noqa: F401
from app.modules.monitoring import models as _monitoring_models  # noqa: F401
from app.modules.observability import models as _observability_models  # noqa: F401
from app.modules.optimization import models as _optimization_models  # noqa: F401
from app.modules.orchestrator import models as _orchestrator_models  # noqa: F401
from app.modules.performance import models as _performance_models  # noqa: F401
from app.modules.pipeline import models as _pipeline_models  # noqa: F401
from app.modules.security import models as _security_models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer DATABASE_URL from the environment (set in .env / shell) over
# the placeholder in alembic.ini, so the same migrations work whether
# Postgres is running natively (localhost) or on Render — routed through
# settings.DATABASE_URL so it gets the same postgres:// -> postgresql+
# psycopg:// normalization (27.8) the app itself uses, instead of a
# second copy of that logic here.
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
