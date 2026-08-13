from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.freshness import compute_freshness
from app.models.electricity_price import ElectricityPrice


def create_price(
    db: Session,
    factory_id: int,
    data,
) -> ElectricityPrice:
    price = ElectricityPrice(
        factory_id=factory_id,
        timestamp=data.timestamp,
        buy_price_per_kwh=data.buy_price_per_kwh,
        sell_price_per_kwh=data.sell_price_per_kwh,
        price_level=data.price_level.value,
    )

    db.add(price)
    db.commit()
    db.refresh(price)

    return price


def get_prices(
    db: Session,
    factory_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[ElectricityPrice]:
    query = (
        select(ElectricityPrice)
        .where(ElectricityPrice.factory_id == factory_id)
        .order_by(ElectricityPrice.timestamp.asc())
    )

    if start:
        query = query.where(ElectricityPrice.timestamp >= start)

    if end:
        query = query.where(ElectricityPrice.timestamp <= end)

    return db.scalars(query).all()


def get_price_analysis(db: Session, factory_id: int) -> dict:
    prices = get_prices(db=db, factory_id=factory_id)

    if not prices:
        return {
            "current": None,
            "cheapest": None,
            "most_expensive": None,
            "current_age_minutes": None,
            "current_is_stale": None,
        }

    cheapest = min(prices, key=lambda x: x.buy_price_per_kwh)
    most_expensive = max(prices, key=lambda x: x.buy_price_per_kwh)
    current = prices[-1]

    freshness = compute_freshness(current.timestamp)

    return {
        "current": current,
        "cheapest": cheapest,
        "most_expensive": most_expensive,
        "current_age_minutes": freshness["age_minutes"],
        "current_is_stale": freshness["is_stale"],
    }


def get_current_price(db: Session, factory_id: int) -> ElectricityPrice | None:
    """
    Used by the battery recommendation (10.19) to pull a real price
    signal instead of the "unknown" placeholder from Step 9.
    """
    return db.scalar(
        select(ElectricityPrice)
        .where(ElectricityPrice.factory_id == factory_id)
        .order_by(ElectricityPrice.timestamp.desc())
        .limit(1)
    )
