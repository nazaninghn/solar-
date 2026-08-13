from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.db_monitoring import register_query_monitoring

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

register_query_monitoring(engine)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
