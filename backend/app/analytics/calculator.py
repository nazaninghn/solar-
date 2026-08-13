from datetime import datetime, timedelta


def calculate_energy_from_power(power_kw: float, duration_hours: float) -> float:
    """22.12, verbatim formula: Energy kWh = Power kW x Duration hours."""
    return round(power_kw * duration_hours, 4)


def aggregate_device_power_to_energy(
    samples: list[tuple[datetime, float]],
    bucket_start: datetime,
    bucket_end: datetime,
    max_hold_hours: float = 0.5,
) -> float:
    """
    22.11-22.14's actual point: raw power samples can't just be summed
    and called kWh — this is real time-weighted (step) integration.
    Never built anywhere before Step 22 — Step 17's aggregation worked
    from EnergyReading, which already stores energy, not power+timestamp
    pairs needing this integration at all.

    Each sample's power is assumed to hold constant until the next
    sample (or bucket_end, or max_hold_hours — whichever is sooner, so a
    single stale reading before a gap doesn't get extrapolated across
    the whole rest of the bucket).
    """
    if not samples:
        return 0.0

    ordered = sorted(samples, key=lambda s: s[0])
    energy_kwh = 0.0

    for i, (timestamp, power_kw) in enumerate(ordered):
        interval_start = max(timestamp, bucket_start)

        if i + 1 < len(ordered):
            next_timestamp = ordered[i + 1][0]
        else:
            next_timestamp = bucket_end

        capped_end = min(
            next_timestamp,
            bucket_end,
            timestamp + timedelta(hours=max_hold_hours),
        )

        if capped_end <= interval_start:
            continue

        duration_hours = (capped_end - interval_start).total_seconds() / 3600
        energy_kwh += calculate_energy_from_power(power_kw, duration_hours)

    return round(energy_kwh, 2)


def validate_power_reading(power_kw: float) -> bool:
    """22.32: a solar/grid power reading below zero is physically invalid."""
    return power_kw >= 0


def validate_soc_reading(soc_percent: float) -> bool:
    """22.32: SOC must be within 0-100%."""
    return 0 <= soc_percent <= 100


def calculate_data_completeness_percent(
    actual_sample_count: int,
    expected_sample_count: int,
) -> float:
    if expected_sample_count <= 0:
        return 0.0

    return round(
        min(100.0, (actual_sample_count / expected_sample_count) * 100), 2
    )


def determine_data_quality(completeness_percent: float, has_invalid_data: bool) -> str:
    """22.34's four statuses."""
    if has_invalid_data:
        return "INVALID"
    if completeness_percent <= 0:
        return "MISSING"
    if completeness_percent >= 95:
        return "GOOD"

    return "PARTIAL"
