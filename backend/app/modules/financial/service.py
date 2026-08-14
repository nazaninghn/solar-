from datetime import date as date_type
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.electricity_price import ElectricityPrice
from app.models.energy_reading import EnergyReading
from app.models.factory import Factory
from app.models.financial_record import FinancialRecord
from app.models.financial_transaction import FinancialTransaction
from app.models.recommendation import Recommendation
from app.modules.financial.calculations import (
    calculate_battery_degradation_cost,
    calculate_battery_savings,
    calculate_change_percent,
    calculate_cost_reduction_percent,
    calculate_energy_sales,
    calculate_grid_cost,
    calculate_grid_dependency_percent,
    calculate_net_battery_saving,
    calculate_net_energy_cost,
    calculate_payback_period_years,
    calculate_roi_percent,
    calculate_solar_contribution_percent,
    calculate_solar_savings,
    calculate_total_savings,
    get_battery_degradation_rate,
)
from app.modules.financial.enums import FinancialTransactionType

# Same MVP placeholder used in the recommendations engine (Step 11) —
# BatterySystem has no stored round-trip efficiency yet.
BATTERY_EFFICIENCY = 0.90

# 21.14 wants a real "Battery Replacement Cost / Expected Lifetime
# Throughput" figure, which nothing in this schema stores yet. Using a
# fixed absolute number (the brief's own "700 Toman/kWh" example) would
# be wrong for a USD-priced factory, so this is expressed as a share of
# the current grid price instead — stays proportional regardless of
# currency, flagged as an MVP placeholder pending real battery cost data.
BATTERY_DEGRADATION_RATE = 0.05


def _day_bounds_utc(target_date: date_type) -> tuple[datetime, datetime]:
    start = datetime(
        target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc
    )
    return start, start + timedelta(days=1)


def _replace_daily_transactions(
    db: Session,
    factory_id: int,
    target_date: date_type,
    items: list[dict],
) -> None:
    """
    21.4-21.6, 21.37-21.38: one ledger row per transaction type per day
    (not per-hour — would be thousands of rows for no real audit
    benefit over the daily-aggregate granularity this engine already
    works at). Deletes and re-inserts for the day so re-running stays
    idempotent, same as the FinancialRecord upsert itself.
    """
    start, end = _day_bounds_utc(target_date)

    db.execute(
        delete(FinancialTransaction).where(
            FinancialTransaction.factory_id == factory_id,
            FinancialTransaction.timestamp >= start,
            FinancialTransaction.timestamp < end,
        )
    )

    now = datetime.now(timezone.utc)

    for item in items:
        if item["energy_kwh"] == 0 and item["amount"] == 0:
            continue

        db.add(
            FinancialTransaction(
                factory_id=factory_id,
                type=item["type"],
                energy_kwh=item["energy_kwh"],
                unit_price=item["unit_price"],
                amount=item["amount"],
                timestamp=start,
                description=item.get("description"),
                created_at=now,
            )
        )


def compute_daily_financial_record(
    db: Session,
    factory_id: int,
    target_date: date_type,
) -> FinancialRecord | None:
    """
    Bridges raw EnergyReading + ElectricityPrice data into a stored
    FinancialRecord for one day, and (Step 21) also writes the
    corresponding FinancialTransaction ledger rows for auditability.
    Upserts by (factory_id, date).
    """
    start, end = _day_bounds_utc(target_date)

    factory = db.get(Factory, factory_id)

    readings = db.scalars(
        select(EnergyReading).where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= start,
            EnergyReading.timestamp < end,
        )
    ).all()

    if not readings:
        return None

    prices = db.scalars(
        select(ElectricityPrice).where(
            ElectricityPrice.factory_id == factory_id,
            ElectricityPrice.timestamp >= start,
            ElectricityPrice.timestamp < end,
        )
    ).all()

    price_by_hour = {p.timestamp.hour: p for p in prices}

    if prices:
        fallback_buy = sum(p.buy_price_per_kwh for p in prices) / len(prices)
        fallback_sell = sum(p.sell_price_per_kwh for p in prices) / len(prices)
    else:
        fallback_buy = 0.0
        fallback_sell = 0.0

    solar_savings = 0.0
    grid_purchase_cost = 0.0
    battery_savings = 0.0
    energy_sales_revenue = 0.0
    battery_degradation_cost = 0.0

    solar_generation_kwh = 0.0
    solar_used_kwh_total = 0.0
    grid_import_kwh_total = 0.0
    grid_export_kwh_total = 0.0

    # Separately weighted per metric — each transaction's stored
    # unit_price must reconcile (energy_kwh * unit_price ~= amount) with
    # what was actually charged for *that* energy flow specifically, not
    # a single day-wide average across a different flow's hours.
    weighted_buy_price_sum = 0.0
    weighted_buy_kwh_sum = 0.0
    weighted_sell_price_sum = 0.0
    weighted_sell_kwh_sum = 0.0
    weighted_solar_price_sum = 0.0
    weighted_solar_kwh_sum = 0.0
    weighted_battery_price_sum = 0.0
    weighted_battery_kwh_sum = 0.0

    for reading in readings:
        price = price_by_hour.get(reading.timestamp.hour)
        buy_price = price.buy_price_per_kwh if price else fallback_buy
        sell_price = price.sell_price_per_kwh if price else fallback_sell

        solar_used_kwh = max(
            0.0,
            reading.consumption_kwh
            - reading.grid_import_kwh
            - reading.battery_discharge_kwh,
        )

        solar_savings += calculate_solar_savings(solar_used_kwh, buy_price)
        grid_purchase_cost += calculate_grid_cost(reading.grid_import_kwh, buy_price)
        battery_savings += calculate_battery_savings(
            reading.battery_discharge_kwh, BATTERY_EFFICIENCY, buy_price
        )
        degradation_rate = get_battery_degradation_rate(
            factory.battery_degradation_cost_per_kwh if factory else None,
            buy_price,
            BATTERY_DEGRADATION_RATE,
        )
        battery_degradation_cost += calculate_battery_degradation_cost(
            reading.battery_discharge_kwh, degradation_rate
        )
        energy_sales_revenue += calculate_energy_sales(
            reading.grid_export_kwh, sell_price
        )

        solar_generation_kwh += reading.solar_generation_kwh
        solar_used_kwh_total += solar_used_kwh
        grid_import_kwh_total += reading.grid_import_kwh
        grid_export_kwh_total += reading.grid_export_kwh

        if reading.grid_import_kwh > 0:
            weighted_buy_price_sum += buy_price * reading.grid_import_kwh
            weighted_buy_kwh_sum += reading.grid_import_kwh
        if reading.grid_export_kwh > 0:
            weighted_sell_price_sum += sell_price * reading.grid_export_kwh
            weighted_sell_kwh_sum += reading.grid_export_kwh
        if solar_used_kwh > 0:
            weighted_solar_price_sum += buy_price * solar_used_kwh
            weighted_solar_kwh_sum += solar_used_kwh
        if reading.battery_discharge_kwh > 0:
            weighted_battery_price_sum += buy_price * reading.battery_discharge_kwh
            weighted_battery_kwh_sum += reading.battery_discharge_kwh

    solar_savings = round(solar_savings, 2)
    grid_purchase_cost = round(grid_purchase_cost, 2)
    battery_savings = round(battery_savings, 2)
    battery_degradation_cost = round(battery_degradation_cost, 2)
    energy_sales_revenue = round(energy_sales_revenue, 2)

    # 20.28-style: attribute realized load-shift savings from
    # recommendations the user actually accepted that day — there's no
    # execution-tracking signal beyond that (Step 20's own 20.33 keeps
    # execution manual/human-approved), so "accepted" is the closest
    # thing to a "this happened" marker available.
    load_shift_savings = db.scalar(
        select(func.coalesce(func.sum(Recommendation.estimated_savings), 0)).where(
            Recommendation.factory_id == factory_id,
            Recommendation.type == "SHIFT_LOAD",
            Recommendation.status == "accepted",
            Recommendation.created_at >= start,
            Recommendation.created_at < end,
        )
    )
    load_shift_savings = round(load_shift_savings or 0.0, 2)

    total_savings = calculate_total_savings(
        solar_savings, battery_savings, energy_sales_revenue
    ) + load_shift_savings
    net_energy_cost = calculate_net_energy_cost(grid_purchase_cost, total_savings)

    record = db.scalar(
        select(FinancialRecord).where(
            FinancialRecord.factory_id == factory_id,
            FinancialRecord.date == target_date,
        )
    )

    if not record:
        record = FinancialRecord(factory_id=factory_id, date=target_date)
        db.add(record)

    record.solar_savings = solar_savings
    record.grid_purchase_cost = grid_purchase_cost
    record.battery_savings = battery_savings
    record.energy_sales_revenue = energy_sales_revenue
    record.total_savings = round(total_savings, 2)
    record.net_energy_cost = net_energy_cost
    record.solar_generation_kwh = round(solar_generation_kwh, 2)
    record.solar_used_kwh = round(solar_used_kwh_total, 2)
    record.grid_import_kwh = round(grid_import_kwh_total, 2)
    record.grid_export_kwh = round(grid_export_kwh_total, 2)
    record.battery_degradation_cost = battery_degradation_cost
    record.load_shift_savings = load_shift_savings
    record.created_at = datetime.now(timezone.utc)

    avg_buy_price = (
        weighted_buy_price_sum / weighted_buy_kwh_sum if weighted_buy_kwh_sum else 0.0
    )
    avg_sell_price = (
        weighted_sell_price_sum / weighted_sell_kwh_sum
        if weighted_sell_kwh_sum
        else 0.0
    )
    avg_solar_price = (
        weighted_solar_price_sum / weighted_solar_kwh_sum
        if weighted_solar_kwh_sum
        else 0.0
    )
    avg_battery_price = (
        weighted_battery_price_sum / weighted_battery_kwh_sum
        if weighted_battery_kwh_sum
        else 0.0
    )

    _replace_daily_transactions(
        db,
        factory_id,
        target_date,
        [
            {
                "type": FinancialTransactionType.GRID_PURCHASE.value,
                "energy_kwh": grid_import_kwh_total,
                "unit_price": round(avg_buy_price, 2),
                "amount": grid_purchase_cost,
                "description": "Daily grid purchase cost",
            },
            {
                "type": FinancialTransactionType.GRID_SALE.value,
                "energy_kwh": grid_export_kwh_total,
                "unit_price": round(avg_sell_price, 2),
                "amount": energy_sales_revenue,
                "description": "Daily grid sale revenue",
            },
            {
                "type": FinancialTransactionType.SOLAR_SAVING.value,
                "energy_kwh": solar_used_kwh_total,
                "unit_price": round(avg_solar_price, 2),
                "amount": solar_savings,
                "description": "Daily solar self-consumption saving",
            },
            {
                "type": FinancialTransactionType.BATTERY_SAVING.value,
                "energy_kwh": sum(r.battery_discharge_kwh for r in readings),
                "unit_price": round(avg_battery_price, 2),
                "amount": calculate_net_battery_saving(
                    battery_savings, battery_degradation_cost
                ),
                "description": (
                    f"Net battery saving (gross {battery_savings}, "
                    f"degradation {battery_degradation_cost})"
                ),
            },
            {
                "type": FinancialTransactionType.LOAD_SHIFT_SAVING.value,
                "energy_kwh": 0.0,
                "unit_price": 0.0,
                "amount": load_shift_savings,
                "description": "Realized savings from accepted SHIFT_LOAD recommendations",
            },
        ],
    )

    db.commit()
    db.refresh(record)

    return record


def ensure_financial_records(
    db: Session,
    factory_id: int,
    start_date: date_type,
    end_date: date_type,
) -> None:
    """
    Computes any missing daily records in the range. Per 12.2's point
    about not recomputing on every dashboard open, existing days are
    left untouched — refreshing a day whose raw data changed after the
    fact is a Step 13 (scheduled jobs) concern, not this one.
    """
    existing_dates = set(
        db.scalars(
            select(FinancialRecord.date).where(
                FinancialRecord.factory_id == factory_id,
                FinancialRecord.date >= start_date,
                FinancialRecord.date <= end_date,
            )
        ).all()
    )

    current = start_date
    while current <= end_date:
        if current not in existing_dates:
            compute_daily_financial_record(db, factory_id, current)
        current += timedelta(days=1)


def get_period_summary(
    db: Session,
    factory_id: int,
    start_date: date_type,
    end_date: date_type,
) -> dict:
    ensure_financial_records(db, factory_id, start_date, end_date)

    result = db.execute(
        select(
            func.coalesce(func.sum(FinancialRecord.solar_savings), 0).label(
                "solar_savings"
            ),
            func.coalesce(func.sum(FinancialRecord.grid_purchase_cost), 0).label(
                "grid_purchase_cost"
            ),
            func.coalesce(func.sum(FinancialRecord.battery_savings), 0).label(
                "battery_savings"
            ),
            func.coalesce(func.sum(FinancialRecord.energy_sales_revenue), 0).label(
                "energy_sales_revenue"
            ),
            func.coalesce(func.sum(FinancialRecord.total_savings), 0).label(
                "total_savings"
            ),
            func.coalesce(func.sum(FinancialRecord.net_energy_cost), 0).label(
                "net_energy_cost"
            ),
            func.coalesce(func.sum(FinancialRecord.load_shift_savings), 0).label(
                "load_shift_savings"
            ),
        ).where(
            FinancialRecord.factory_id == factory_id,
            FinancialRecord.date >= start_date,
            FinancialRecord.date <= end_date,
        )
    ).one()

    period_length = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_length - 1)

    ensure_financial_records(db, factory_id, previous_start, previous_end)

    previous_total_savings = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.total_savings), 0)).where(
            FinancialRecord.factory_id == factory_id,
            FinancialRecord.date >= previous_start,
            FinancialRecord.date <= previous_end,
        )
    )

    baseline_cost = (
        result.grid_purchase_cost + result.solar_savings + result.battery_savings
    )

    return {
        "solar_savings": result.solar_savings,
        "grid_purchase_cost": result.grid_purchase_cost,
        "battery_savings": result.battery_savings,
        "energy_sales_revenue": result.energy_sales_revenue,
        "load_shift_savings": result.load_shift_savings,
        "total_savings": result.total_savings,
        "total_revenue": result.energy_sales_revenue,
        "net_energy_cost": result.net_energy_cost,
        "previous_period_savings": previous_total_savings,
        "savings_change_percent": calculate_change_percent(
            result.total_savings, previous_total_savings
        ),
        "cost_reduction_percent": calculate_cost_reduction_percent(
            baseline_cost, result.grid_purchase_cost
        ),
    }


def get_monthly_history(
    db: Session,
    factory_id: int,
    months: int = 6,
) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    first_of_this_month = today.replace(day=1)

    month_starts = []
    cursor = first_of_this_month
    for _ in range(months):
        month_starts.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    month_starts.reverse()

    results = []

    for month_start in month_starts:
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
        month_end = next_month_start - timedelta(days=1)

        ensure_financial_records(db, factory_id, month_start, month_end)

        row = db.execute(
            select(
                func.coalesce(func.sum(FinancialRecord.grid_purchase_cost), 0).label(
                    "grid_purchase_cost"
                ),
                func.coalesce(func.sum(FinancialRecord.total_savings), 0).label(
                    "total_savings"
                ),
                func.coalesce(
                    func.sum(FinancialRecord.energy_sales_revenue), 0
                ).label("energy_sales_revenue"),
            ).where(
                FinancialRecord.factory_id == factory_id,
                FinancialRecord.date >= month_start,
                FinancialRecord.date <= month_end,
            )
        ).one()

        results.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "grid_purchase_cost": row.grid_purchase_cost,
                "total_savings": row.total_savings,
                "energy_sales_revenue": row.energy_sales_revenue,
            }
        )

    return results


def get_financial_kpis(
    db: Session,
    factory: Factory,
    start_date: date_type,
    end_date: date_type,
) -> dict:
    ensure_financial_records(db, factory.id, start_date, end_date)

    result = db.execute(
        select(
            func.coalesce(func.sum(FinancialRecord.solar_used_kwh), 0).label(
                "solar_used_kwh"
            ),
            func.coalesce(func.sum(FinancialRecord.grid_import_kwh), 0).label(
                "grid_import_kwh"
            ),
            func.coalesce(
                func.sum(
                    FinancialRecord.solar_used_kwh + FinancialRecord.grid_import_kwh
                ),
                0,
            ).label("consumption_kwh"),
            func.coalesce(func.sum(FinancialRecord.total_savings), 0).label(
                "total_savings"
            ),
            func.coalesce(func.sum(FinancialRecord.energy_sales_revenue), 0).label(
                "energy_sales_revenue"
            ),
        ).where(
            FinancialRecord.factory_id == factory.id,
            FinancialRecord.date >= start_date,
            FinancialRecord.date <= end_date,
        )
    ).one()

    solar_contribution = calculate_solar_contribution_percent(
        result.solar_used_kwh, result.consumption_kwh
    )
    grid_dependency = calculate_grid_dependency_percent(
        result.grid_import_kwh, result.consumption_kwh
    )
    renewable_coverage = solar_contribution

    period_days = (end_date - start_date).days + 1
    annual_benefit = (
        (result.total_savings + result.energy_sales_revenue) / period_days * 365
        if period_days > 0
        else 0.0
    )

    roi_percent = calculate_roi_percent(
        annual_benefit, factory.solar_installation_cost
    )
    payback_years = calculate_payback_period_years(
        factory.solar_installation_cost, annual_benefit
    )

    return {
        "solar_contribution_percent": solar_contribution,
        "grid_dependency_percent": grid_dependency,
        "renewable_coverage_percent": renewable_coverage,
        "estimated_annual_benefit": round(annual_benefit, 2),
        "estimated_roi_percent": roi_percent,
        "estimated_payback_years": payback_years,
    }


def get_transactions(
    db: Session,
    factory_id: int,
    start: datetime,
    end: datetime,
    transaction_type: str | None = None,
) -> list[FinancialTransaction]:
    query = select(FinancialTransaction).where(
        FinancialTransaction.factory_id == factory_id,
        FinancialTransaction.timestamp >= start,
        FinancialTransaction.timestamp <= end,
    )

    if transaction_type:
        query = query.where(FinancialTransaction.type == transaction_type)

    return db.scalars(query.order_by(FinancialTransaction.timestamp.desc())).all()
