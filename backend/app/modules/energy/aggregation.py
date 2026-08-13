from datetime import date as date_type, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.calculator import (
    aggregate_device_power_to_energy,
    calculate_data_completeness_percent,
    determine_data_quality,
)
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.energy_daily import EnergyDaily
from app.models.energy_hourly import EnergyHourly
from app.models.energy_monthly import EnergyMonthly
from app.models.energy_reading import EnergyReading
from app.models.financial_record import FinancialRecord

DEVICE_AGGREGATED_SOURCE = "DEVICE_AGGREGATED"


def sync_device_readings_to_energy_reading(
    db: Session,
    factory_id: int,
    hour_start: datetime,
) -> EnergyReading | None:
    """
    Step 26's aggregation-gap fix. Device polling (and the telemetry-
    ingestion endpoint) writes per-device power samples into
    DeviceEnergyReading, but aggregate_factory_hour below only ever
    reads the older, factory-level EnergyReading table (Step 7) —
    without this, live device telemetry would never reach hourly/daily/
    monthly history, analytics, or financial calculations.

    Uses aggregate_device_power_to_energy (built in Step 22, never
    wired to anything until now) for real time-weighted integration —
    naively summing power_kw samples would wildly overcount energy for
    a device polled every 5 seconds.

    Writes one canonical EnergyReading row per factory per hour
    (source="DEVICE_AGGREGATED", timestamp=hour_start), upserted so
    re-running this for an already-synced hour recomputes rather than
    duplicates — the same idempotency shape as aggregate_factory_hour
    itself.
    """
    hour_end = hour_start + timedelta(hours=1)

    rows = db.execute(
        select(DeviceEnergyReading, Device.device_type)
        .join(Device, Device.id == DeviceEnergyReading.device_id)
        .where(
            DeviceEnergyReading.factory_id == factory_id,
            DeviceEnergyReading.timestamp >= hour_start,
            DeviceEnergyReading.timestamp < hour_end,
        )
    ).all()

    if not rows:
        return None

    # Samples grouped per individual device — each device's own power
    # must be integrated as its own continuous series before summing
    # across devices of the same type (two inverters averaged together
    # would misrepresent both).
    samples_by_device: dict[int, list[tuple[datetime, float]]] = {}
    import_samples_by_device: dict[int, list[tuple[datetime, float]]] = {}
    export_samples_by_device: dict[int, list[tuple[datetime, float]]] = {}
    device_types: dict[int, str] = {}
    latest_battery_soc: float | None = None
    latest_battery_timestamp: datetime | None = None

    for reading, device_type in rows:
        device_types[reading.device_id] = device_type
        samples_by_device.setdefault(reading.device_id, []).append(
            (reading.timestamp, reading.power_kw)
        )

        if device_type == "GRID_METER" and reading.raw_data:
            if "import_power_kw" in reading.raw_data:
                import_samples_by_device.setdefault(reading.device_id, []).append(
                    (reading.timestamp, reading.raw_data["import_power_kw"])
                )
            if "export_power_kw" in reading.raw_data:
                export_samples_by_device.setdefault(reading.device_id, []).append(
                    (reading.timestamp, reading.raw_data["export_power_kw"])
                )

        if device_type == "BATTERY" and reading.soc_percent is not None:
            if latest_battery_timestamp is None or reading.timestamp > latest_battery_timestamp:
                latest_battery_timestamp = reading.timestamp
                latest_battery_soc = reading.soc_percent

    solar_generation_kwh = 0.0
    consumption_kwh = 0.0
    grid_import_kwh = 0.0
    grid_export_kwh = 0.0
    battery_charge_kwh = 0.0
    battery_discharge_kwh = 0.0

    for device_id, samples in samples_by_device.items():
        device_type = device_types[device_id]

        if device_type == "INVERTER":
            solar_generation_kwh += aggregate_device_power_to_energy(
                samples, hour_start, hour_end
            )
        elif device_type == "FACTORY_METER":
            consumption_kwh += aggregate_device_power_to_energy(
                samples, hour_start, hour_end
            )
        elif device_type == "BATTERY":
            # 26.20's convention: positive net = charging, negative = a
            # net discharge for the hour. A battery that both charges
            # and discharges within the same hour nets out here, same
            # simplification a real inverter's own hourly totalizer
            # typically makes.
            net_kwh = aggregate_device_power_to_energy(samples, hour_start, hour_end)
            if net_kwh >= 0:
                battery_charge_kwh += net_kwh
            else:
                battery_discharge_kwh += abs(net_kwh)
        elif device_type == "GRID_METER":
            if device_id in import_samples_by_device or device_id in export_samples_by_device:
                # Genuine separate import/export series were captured
                # (raw_data) — integrate each independently rather than
                # inferring from the net.
                grid_import_kwh += aggregate_device_power_to_energy(
                    import_samples_by_device.get(device_id, []), hour_start, hour_end
                )
                grid_export_kwh += aggregate_device_power_to_energy(
                    export_samples_by_device.get(device_id, []), hour_start, hour_end
                )
            else:
                net_kwh = aggregate_device_power_to_energy(samples, hour_start, hour_end)
                if net_kwh >= 0:
                    grid_import_kwh += net_kwh
                else:
                    grid_export_kwh += abs(net_kwh)

    existing = db.scalar(
        select(EnergyReading).where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp == hour_start,
            EnergyReading.source == DEVICE_AGGREGATED_SOURCE,
        )
    )

    if existing:
        row = existing
    else:
        row = EnergyReading(
            factory_id=factory_id,
            timestamp=hour_start,
            source=DEVICE_AGGREGATED_SOURCE,
        )
        db.add(row)

    row.solar_generation_kwh = round(solar_generation_kwh, 2)
    row.consumption_kwh = round(consumption_kwh, 2)
    row.grid_import_kwh = round(grid_import_kwh, 2)
    row.grid_export_kwh = round(grid_export_kwh, 2)
    row.battery_charge_kwh = round(battery_charge_kwh, 2)
    row.battery_discharge_kwh = round(battery_discharge_kwh, 2)
    row.battery_soc_percent = latest_battery_soc

    db.commit()
    db.refresh(row)

    return row


def aggregate_factory_hour(
    db: Session,
    factory_id: int,
    hour_start: datetime,
) -> EnergyHourly | None:
    """
    Sums raw EnergyReading rows (the existing factory-level table, Step 7)
    that fall in [hour_start, hour_start + 1h) into one EnergyHourly row.
    Upserts by the (factory_id, hour) unique constraint, so re-running
    this for an hour that's already aggregated just recomputes it rather
    than duplicating (17.18).

    Returns None — and does not create a row — if there were zero raw
    readings for the hour, so "missing" (17.27) is represented by the
    row's absence rather than a fabricated zero-value row.
    """
    hour_end = hour_start + timedelta(hours=1)

    readings = db.scalars(
        select(EnergyReading).where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= hour_start,
            EnergyReading.timestamp < hour_end,
        )
    ).all()

    if not readings:
        return None

    # 22.32: EnergyReadingCreate already rejects negative values at the
    # API boundary (Field(ge=0)), so this mainly guards data that could
    # arrive some other way (direct DB writes, future ingestion paths).
    has_invalid_data = any(
        r.solar_generation_kwh < 0 or r.consumption_kwh < 0 for r in readings
    )

    solar_kwh = sum(r.solar_generation_kwh for r in readings)
    consumption_kwh = sum(r.consumption_kwh for r in readings)
    grid_import_kwh = sum(r.grid_import_kwh for r in readings)
    grid_export_kwh = sum(r.grid_export_kwh for r in readings)
    battery_charge_kwh = sum(r.battery_charge_kwh for r in readings)
    battery_discharge_kwh = sum(r.battery_discharge_kwh for r in readings)

    existing = db.scalar(
        select(EnergyHourly).where(
            EnergyHourly.factory_id == factory_id,
            EnergyHourly.hour == hour_start,
        )
    )

    if existing:
        row = existing
    else:
        row = EnergyHourly(factory_id=factory_id, hour=hour_start)
        db.add(row)

    # This system's raw EnergyReading rows arrive roughly one per hour
    # (POST /energy/readings), not per-minute — so "expected" for a
    # single-hour bucket is 1, not some higher per-minute sample count
    # that doesn't reflect how this data actually gets produced.
    completeness = calculate_data_completeness_percent(len(readings), 1)

    row.solar_kwh = round(solar_kwh, 2)
    row.consumption_kwh = round(consumption_kwh, 2)
    row.grid_import_kwh = round(grid_import_kwh, 2)
    row.grid_export_kwh = round(grid_export_kwh, 2)
    row.battery_charge_kwh = round(battery_charge_kwh, 2)
    row.battery_discharge_kwh = round(battery_discharge_kwh, 2)
    row.data_completeness = completeness
    row.data_quality = determine_data_quality(completeness, has_invalid_data)

    db.commit()
    db.refresh(row)

    return row


def aggregate_factory_day(
    db: Session,
    factory_id: int,
    day: date_type,
) -> EnergyDaily | None:
    """
    Sums EnergyHourly rows (not raw readings again) for the given date,
    per 17.15's Raw -> Hourly -> Daily pipeline. Peak demand/solar are
    read from the raw EnergyReading rows directly, since EnergyHourly
    only carries sums, not per-reading maxima.
    """
    day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    result = db.execute(
        select(
            func.coalesce(func.sum(EnergyHourly.solar_kwh), 0).label("solar_kwh"),
            func.coalesce(func.sum(EnergyHourly.consumption_kwh), 0).label(
                "consumption_kwh"
            ),
            func.coalesce(func.sum(EnergyHourly.grid_import_kwh), 0).label(
                "grid_import_kwh"
            ),
            func.coalesce(func.sum(EnergyHourly.grid_export_kwh), 0).label(
                "grid_export_kwh"
            ),
            func.coalesce(func.sum(EnergyHourly.battery_charge_kwh), 0).label(
                "battery_charge_kwh"
            ),
            func.coalesce(func.sum(EnergyHourly.battery_discharge_kwh), 0).label(
                "battery_discharge_kwh"
            ),
            func.count(EnergyHourly.id).label("hour_count"),
            func.bool_or(EnergyHourly.data_quality == "INVALID").label(
                "has_invalid_data"
            ),
        ).where(
            EnergyHourly.factory_id == factory_id,
            EnergyHourly.hour >= day_start,
            EnergyHourly.hour < day_end,
        )
    ).one()

    if result.hour_count == 0:
        return None

    # 22.21: peak demand/solar — the highest single hourly reading in the
    # day, and when it happened. This system's raw granularity is
    # hourly, not truly instantaneous, so "peak" here means "the hour
    # with the highest value" rather than a sub-hourly spike.
    peak_reading = db.scalar(
        select(EnergyReading)
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= day_start,
            EnergyReading.timestamp < day_end,
        )
        .order_by(EnergyReading.consumption_kwh.desc())
        .limit(1)
    )
    peak_solar_reading = db.scalar(
        select(EnergyReading)
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= day_start,
            EnergyReading.timestamp < day_end,
        )
        .order_by(EnergyReading.solar_generation_kwh.desc())
        .limit(1)
    )

    existing = db.scalar(
        select(EnergyDaily).where(
            EnergyDaily.factory_id == factory_id,
            EnergyDaily.date == day,
        )
    )

    if existing:
        row = existing
    else:
        row = EnergyDaily(factory_id=factory_id, date=day)
        db.add(row)

    completeness = calculate_data_completeness_percent(result.hour_count, 24)

    row.solar_kwh = round(result.solar_kwh, 2)
    row.consumption_kwh = round(result.consumption_kwh, 2)
    row.grid_import_kwh = round(result.grid_import_kwh, 2)
    row.grid_export_kwh = round(result.grid_export_kwh, 2)
    row.battery_charge_kwh = round(result.battery_charge_kwh, 2)
    row.battery_discharge_kwh = round(result.battery_discharge_kwh, 2)
    row.data_completeness = completeness
    row.data_quality = determine_data_quality(
        completeness, bool(result.has_invalid_data)
    )
    row.peak_demand_kw = peak_reading.consumption_kwh if peak_reading else None
    row.peak_demand_time = peak_reading.timestamp if peak_reading else None
    row.peak_solar_kw = (
        peak_solar_reading.solar_generation_kwh if peak_solar_reading else None
    )

    db.commit()
    db.refresh(row)

    return row


def aggregate_factory_month(
    db: Session,
    factory_id: int,
    month_start: date_type,
) -> EnergyMonthly | None:
    """Sums EnergyDaily rows for the month, completing the Step 22 pipeline."""
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    result = db.execute(
        select(
            func.coalesce(func.sum(EnergyDaily.solar_kwh), 0).label("solar_kwh"),
            func.coalesce(func.sum(EnergyDaily.consumption_kwh), 0).label(
                "consumption_kwh"
            ),
            func.coalesce(func.sum(EnergyDaily.grid_import_kwh), 0).label(
                "grid_import_kwh"
            ),
            func.coalesce(func.sum(EnergyDaily.grid_export_kwh), 0).label(
                "grid_export_kwh"
            ),
            func.count(EnergyDaily.id).label("day_count"),
        ).where(
            EnergyDaily.factory_id == factory_id,
            EnergyDaily.date >= month_start,
            EnergyDaily.date < next_month_start,
        )
    ).one()

    if result.day_count == 0:
        return None

    # 22.39: Analytics must not recompute pricing itself — it consumes
    # the Financial Engine's own daily snapshots (Step 12) for the
    # dollar figures rather than re-deriving them from raw energy data.
    financial_result = db.execute(
        select(
            func.coalesce(func.sum(FinancialRecord.total_savings), 0).label(
                "total_savings"
            ),
            func.coalesce(func.sum(FinancialRecord.energy_sales_revenue), 0).label(
                "total_revenue"
            ),
        ).where(
            FinancialRecord.factory_id == factory_id,
            FinancialRecord.date >= month_start,
            FinancialRecord.date < next_month_start,
        )
    ).one()

    days_in_month = (next_month_start - month_start).days
    month_key = month_start.strftime("%Y-%m")

    existing = db.scalar(
        select(EnergyMonthly).where(
            EnergyMonthly.factory_id == factory_id,
            EnergyMonthly.month == month_key,
        )
    )

    if existing:
        row = existing
    else:
        row = EnergyMonthly(factory_id=factory_id, month=month_key)
        db.add(row)

    row.solar_kwh = round(result.solar_kwh, 2)
    row.consumption_kwh = round(result.consumption_kwh, 2)
    row.grid_import_kwh = round(result.grid_import_kwh, 2)
    row.grid_export_kwh = round(result.grid_export_kwh, 2)
    row.total_savings = round(financial_result.total_savings, 2)
    row.total_revenue = round(financial_result.total_revenue, 2)
    row.data_completeness = calculate_data_completeness_percent(
        result.day_count, days_in_month
    )

    db.commit()
    db.refresh(row)

    return row
