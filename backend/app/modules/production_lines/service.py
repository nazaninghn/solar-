from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production_line import ProductionLine


def create_production_line(db: Session, factory_id: int, data) -> ProductionLine:
    line = ProductionLine(
        factory_id=factory_id,
        name=data.name,
        power_kw=data.power_kw,
        flexible=data.flexible,
        minimum_run_time_hours=data.minimum_run_time_hours,
        priority=data.priority,
        created_at=datetime.now(timezone.utc),
    )

    db.add(line)
    db.commit()
    db.refresh(line)

    return line


def get_production_lines(db: Session, factory_id: int) -> list[ProductionLine]:
    return db.scalars(
        select(ProductionLine).where(ProductionLine.factory_id == factory_id)
    ).all()
