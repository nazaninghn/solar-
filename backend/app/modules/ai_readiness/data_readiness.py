"""
STEP 81: real data-readiness scoring — per factory, how much clean
historical data actually exists, against a documented minimum needed
before training any real forecasting model would be defensible.
Nothing here trains anything; it answers "could we, today" with a real
number instead of a guess.
"""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.energy_daily import EnergyDaily
from app.models.factory import Factory

# 81: a commonly-cited rule of thumb for daily-granularity time series
# forecasting is a full seasonal cycle (a year) for anything claiming
# to capture seasonality, with 90 days as a bare floor for a
# non-seasonal baseline comparison. Documented default, not a proven
# threshold for this specific business — tunable once a real model is
# actually being evaluated against it.
MIN_DAYS_FOR_BASELINE_COMPARISON = 90
MIN_DAYS_FOR_SEASONAL_MODEL = 365


def compute_data_readiness(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            EnergyDaily.factory_id,
            func.count(EnergyDaily.id),
            func.min(EnergyDaily.date),
            func.max(EnergyDaily.date),
            # Postgres AVG() has no boolean overload — case() maps
            # COMPLETE rows to 1.0/0.0 first so avg() has a numeric
            # column to work with.
            func.avg(case((EnergyDaily.data_quality == "COMPLETE", 1.0), else_=0.0)),
        ).group_by(EnergyDaily.factory_id)
    ).all()

    factory_names = dict(db.execute(select(Factory.id, Factory.name)).all())

    results = []
    for factory_id, sample_count, earliest, latest, complete_ratio in rows:
        span_days = (latest - earliest).days + 1 if earliest and latest else 0

        results.append(
            {
                "factory_id": factory_id,
                "factory_name": factory_names.get(factory_id, "Unknown"),
                "sample_count": sample_count,
                "span_days": span_days,
                "complete_data_ratio": round(float(complete_ratio or 0), 3),
                "ready_for_baseline_comparison": span_days >= MIN_DAYS_FOR_BASELINE_COMPARISON,
                "ready_for_seasonal_model": span_days >= MIN_DAYS_FOR_SEASONAL_MODEL,
            }
        )

    return sorted(results, key=lambda r: r["span_days"], reverse=True)


def compute_platform_readiness_summary(db: Session) -> dict:
    per_factory = compute_data_readiness(db)

    return {
        "total_factories_with_data": len(per_factory),
        "ready_for_baseline_comparison": sum(
            1 for f in per_factory if f["ready_for_baseline_comparison"]
        ),
        "ready_for_seasonal_model": sum(1 for f in per_factory if f["ready_for_seasonal_model"]),
        "min_days_for_baseline_comparison": MIN_DAYS_FOR_BASELINE_COMPARISON,
        "min_days_for_seasonal_model": MIN_DAYS_FOR_SEASONAL_MODEL,
    }
