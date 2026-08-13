def calculate_solar_power(
    capacity_kwp: float,
    irradiance_w_m2: float,
    performance_ratio: float = 0.85,
):
    irradiance_factor = irradiance_w_m2 / 1000

    power = capacity_kwp * irradiance_factor * performance_ratio

    # 19.17's own code doesn't include this despite 19.19 explicitly
    # requiring it — power must never exceed the panel's nameplate
    # capacity, no matter how high irradiance reads.
    power = min(power, capacity_kwp)

    return max(power, 0)


def calculate_forecast_confidence(cloud_cover_percent: float) -> float:
    """
    Not given a formula in the brief — 19.20 only shows two example
    numbers (92% clear, 68% heavy clouds) without deriving them. Reuses
    the same bucket thresholds as the weather condition mapping
    (app/weather/providers/open_meteo_provider.py) so "why is this
    forecast only 68% confident" always traces back to a visible cloud
    cover reading.
    """
    if cloud_cover_percent <= 10:
        return 0.92
    if cloud_cover_percent <= 30:
        return 0.88
    if cloud_cover_percent <= 50:
        return 0.82
    if cloud_cover_percent <= 70:
        return 0.75
    if cloud_cover_percent <= 90:
        return 0.68
    return 0.60
