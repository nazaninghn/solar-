"""
Synthetic site telemetry — a stand-in for real devices until a factory
is connected.

Produces the same per-device samples real hardware pushes through
POST /devices/{id}/telemetry (power, voltage, frequency, temperature,
SOC, plus manufacturer extras in raw_data), so everything downstream —
hourly aggregation, analytics, failure prediction, the sell-offer
builder — runs on it unchanged. Replacing it with real telemetry means
real devices write those rows instead; nothing here is imported by
production code paths.

Physics, kept simple but consistent:
  - irradiance: clear-sky GHI from solar geometry at the site's
    lat/lon (Haurwitz model) x a daily clearness index that persists
    across days (AR(1)), with intra-hour flicker on broken-cloud days,
    x a flat tilt gain for plane-of-array
  - PV: rated x irradiance/1000 x performance ratio x temperature
    derating (-0.4 %/°C above 25 °C cell temp), clipped at AC rating;
    one inverter can soil, its PR decaying linearly over the period
  - load: industrial shift pattern (weekday day shift with lunch dip,
    half Saturday, Sunday/holiday base load) + noise
  - battery: stores PV surplus, discharges into the 17-22 h evening
    peak, within power/SOC limits, sqrt(round-trip) loss each way
  - grid: whatever balances the site —
        pv + import + discharge = load + export + charge
    exactly, so the pipeline's energy-balance check passes

Every sample is a pure function of (spec, timestamp, seed), so an
extension run appends seamlessly to a backfill.
"""

import math
from dataclasses import dataclass, field

import holidays
import numpy as np
import pandas as pd

SYNTHETIC_MARKER = "SYNTHETIC"
POA_GAIN = 1.12

_TR_HOLIDAYS = holidays.Turkey(years=range(2020, 2036))


@dataclass
class InverterSpec:
    key: str
    name: str
    rated_kw: float
    pr: float = 0.82
    # PR lost per day of soiling, counted from `soiling_start`.
    soiling_per_day: float = 0.0
    temp_offset_c: float = 0.0


@dataclass
class BatterySpec:
    capacity_kwh: float = 1200.0
    min_soc: float = 10.0
    max_soc: float = 95.0
    power_kw: float = 400.0
    round_trip_eff: float = 0.90


@dataclass
class SiteSpec:
    latitude: float = 37.87  # Konya
    longitude: float = 32.48
    timezone: str = "Europe/Istanbul"
    inverters: list[InverterSpec] = field(default_factory=lambda: [
        InverterSpec("inverter_a", "Inverter A", 500.0, pr=0.82),
        InverterSpec("inverter_b", "Inverter B", 500.0, pr=0.80, soiling_per_day=0.012, temp_offset_c=4.0),
    ])
    battery: BatterySpec = field(default_factory=BatterySpec)
    # Sized so a clear weekday midday exports: PV > daytime load is
    # the typical rooftop-factory case the sell offer exists for.
    peak_load_kw: float = 450.0
    base_load_fraction: float = 0.22
    soiling_start: pd.Timestamp | None = None
    seed: int = 7


def _solar_elevation_sin(ts_utc: pd.DatetimeIndex, lat: float, lon: float) -> np.ndarray:
    doy = ts_utc.dayofyear.to_numpy()
    hours = ts_utc.hour.to_numpy() + ts_utc.minute.to_numpy() / 60
    decl = np.radians(23.44) * np.sin(np.radians(360 / 365 * (doy - 81)))
    b = np.radians(360 / 365 * (doy - 81))
    eot_min = 9.87 * np.sin(2 * b) - 7.53 * np.cos(b) - 1.5 * np.sin(b)
    solar_time = hours + lon / 15 + eot_min / 60
    hour_angle = np.radians(15 * (solar_time - 12))
    phi = np.radians(lat)
    return np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(hour_angle)


def _daily_clearness(days: pd.DatetimeIndex, seed: int) -> pd.Series:
    """AR(1) over calendar days anchored at a fixed origin, so any
    window of days gets the same values regardless of where it starts."""
    origin = pd.Timestamp("2020-01-01")
    idx = ((days.tz_localize(None) - origin).days).to_numpy()
    rng = np.random.default_rng(seed)
    n = int(idx.max()) + 1
    shocks = rng.normal(0, 1, n)
    z = np.zeros(n)
    for i in range(1, n):
        z[i] = 0.6 * z[i - 1] + 0.8 * shocks[i]
    k = 0.62 + 0.3 * np.tanh(0.7 * z + 0.9)  # mostly sunny, some overcast days
    return pd.Series(np.clip(k[idx], 0.2, 1.0), index=days)


def _splitmix64(x: np.ndarray) -> np.ndarray:
    x = (x + np.uint64(0x9E3779B97F4A7C15)).astype(np.uint64)
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


def _noise(ts_utc: pd.DatetimeIndex, seed: int, salt: int) -> np.ndarray:
    """Per-timestamp standard normal noise that depends only on (minute,
    seed, salt) — stable across runs and window boundaries. Hash-based
    (splitmix64 -> two uniforms -> Box-Muller), fully vectorised."""
    with np.errstate(over="ignore"):
        minutes = (ts_utc.asi8 // 60_000_000_000).astype(np.uint64)
        base = minutes * np.uint64(1_000_003) + np.uint64(salt * 7919 + seed * 104_729)
        u1 = (_splitmix64(base) >> np.uint64(11)).astype(np.float64) / 2**53
        u2 = (_splitmix64(base ^ np.uint64(0xD1B54A32D192ED03)) >> np.uint64(11)).astype(np.float64) / 2**53
    return np.sqrt(-2 * np.log(np.clip(u1, 1e-12, 1))) * np.cos(2 * np.pi * u2)


def simulate(spec: SiteSpec, start: pd.Timestamp, end: pd.Timestamp, step: str = "5min") -> dict[str, pd.DataFrame]:
    """Samples in [start, end) at `step`. Returns one DataFrame per
    device key: inverter keys, "battery", "factory_meter", "grid_meter";
    columns map 1:1 onto DeviceEnergyReading fields + `raw_data`."""
    # Callers pass DB timestamps, which come back in the DB session's
    # timezone — normalise everything to UTC before building the grid.
    start, end = (
        pd.Timestamp(t).tz_convert("UTC") if pd.Timestamp(t).tzinfo else pd.Timestamp(t).tz_localize("UTC")
        for t in (start, end)
    )
    ts = pd.date_range(start, end, freq=step, inclusive="left")
    if len(ts) == 0:
        return {}
    local = ts.tz_convert(spec.timezone)
    hours = local.hour.to_numpy() + local.minute.to_numpy() / 60
    step_h = pd.Timedelta(step).total_seconds() / 3600

    # --- Weather ---
    sin_el = _solar_elevation_sin(ts, spec.latitude, spec.longitude)
    cos_z = np.clip(sin_el, 0, None)
    ghi_clear = np.where(cos_z > 0.01, 1098 * cos_z * np.exp(-0.057 / np.maximum(cos_z, 0.01)), 0.0)
    days = local.normalize()
    k_day = _daily_clearness(days.unique(), spec.seed).reindex(days).to_numpy()
    flicker = np.clip(1 + (1 - k_day) * 0.6 * _noise(ts, spec.seed, 1), 0.15, 1.15)
    # Plane-of-array for a fixed ~30° south tilt: GHI plus a flat gain,
    # coarse but keeps daily yield in the right range for the latitude.
    irradiance = np.clip(ghi_clear * k_day * flicker * POA_GAIN, 0, None)

    doy = local.dayofyear.to_numpy()
    seasonal_mean = 12 - 11 * np.cos(2 * np.pi * (doy - 15) / 365)
    ambient = seasonal_mean + 6 * np.sin(2 * np.pi * (hours - 9) / 24) + 0.8 * _noise(ts, spec.seed, 2)
    module_temp = ambient + irradiance * (45 - 20) / 800

    out: dict[str, pd.DataFrame] = {}
    soiling_origin = spec.soiling_start if spec.soiling_start is not None else ts[0]
    days_since = np.clip((ts - soiling_origin).total_seconds().to_numpy() / 86400, 0, None)

    pv_total = np.zeros(len(ts))
    for n, inv in enumerate(spec.inverters):
        pr = np.clip(inv.pr - inv.soiling_per_day * days_since, 0.3, 1.0)
        derate = 1 - 0.004 * np.clip(module_temp - 25, 0, None)
        dc_kw = inv.rated_kw * irradiance / 1000 * pr * derate * (1 + 0.01 * _noise(ts, spec.seed, 10 + n))
        ac_kw = np.clip(dc_kw * 0.97, 0, inv.rated_kw)
        pv_total += ac_kw
        inv_temp = ambient + 18 * ac_kw / inv.rated_kw + inv.temp_offset_c + 0.5 * _noise(ts, spec.seed, 20 + n)
        voltage = 400 + 3.0 * _noise(ts, spec.seed, 30 + n)
        freq = 50 + 0.02 * _noise(ts, spec.seed, 40 + n)
        out[inv.key] = pd.DataFrame({
            "timestamp": ts,
            "power_kw": np.round(ac_kw, 3),
            "voltage": np.round(voltage, 2),
            "current": np.round(ac_kw * 1000 / (math.sqrt(3) * voltage), 2),
            "frequency": np.round(freq, 3),
            "temperature_c": np.round(inv_temp, 2),
            "soc_percent": np.nan,
            "raw_data": [
                {
                    "source": SYNTHETIC_MARKER,
                    "irradiance_w_m2": round(float(g), 1),
                    "ambient_temp_c": round(float(a), 2),
                    "module_temp_c": round(float(mt), 2),
                    "dc_power_kw": round(float(d), 3),
                    "rated_power_kw": inv.rated_kw,
                }
                for g, a, mt, d in zip(irradiance, ambient, module_temp, dc_kw)
            ],
        })

    # --- Load ---
    dow = local.dayofweek.to_numpy()
    is_holiday = np.array([d.date() in _TR_HOLIDAYS for d in days])
    shift = ((hours >= 7) & (hours < 19)).astype(float)
    ramp = np.clip(np.minimum(hours - 6, 20 - hours), 0, 1)
    lunch = np.where((hours >= 12) & (hours < 13), 0.75, 1.0)
    day_factor = np.where(is_holiday | (dow == 6), 0.0, np.where(dow == 5, 0.5, 1.0))
    base = spec.base_load_fraction * spec.peak_load_kw
    load = base + (spec.peak_load_kw - base) * shift * ramp * lunch * day_factor
    load = np.clip(load * (1 + 0.05 * _noise(ts, spec.seed, 50)), 0.5 * base, None)

    # --- Battery (sequential SOC) ---
    b = spec.battery
    eff_leg = math.sqrt(b.round_trip_eff)
    soc_kwh = b.capacity_kwh * (b.min_soc + 20) / 100  # arbitrary but fixed opening state
    lo, hi = b.capacity_kwh * b.min_soc / 100, b.capacity_kwh * b.max_soc / 100
    charge = np.zeros(len(ts))
    discharge = np.zeros(len(ts))
    soc_pct = np.zeros(len(ts))
    for i in range(len(ts)):
        surplus = pv_total[i] - load[i]
        if surplus > 0:
            c = min(surplus, b.power_kw, (hi - soc_kwh) / (step_h * eff_leg))
            charge[i] = max(c, 0.0)
            soc_kwh += charge[i] * step_h * eff_leg
        elif 17 <= hours[i] < 22:
            d = min(-surplus, b.power_kw, (soc_kwh - lo) * eff_leg / step_h)
            discharge[i] = max(d, 0.0)
            soc_kwh -= discharge[i] * step_h / eff_leg
        soc_pct[i] = 100 * soc_kwh / b.capacity_kwh
    batt_temp = 24 + 0.35 * (ambient - 20) + 4 * (charge + discharge) / b.power_kw

    out["battery"] = pd.DataFrame({
        "timestamp": ts,
        "power_kw": np.round(charge - discharge, 3),  # + charging, - discharging
        "voltage": np.round(760 + 0.4 * (soc_pct - 50) + _noise(ts, spec.seed, 60), 2),
        "current": np.nan,
        "frequency": np.nan,
        "temperature_c": np.round(batt_temp, 2),
        "soc_percent": np.round(soc_pct, 2),
        "raw_data": [{"source": SYNTHETIC_MARKER}] * len(ts),
    })

    grid_net = load + charge - pv_total - discharge
    grid_import = np.clip(grid_net, 0, None)
    grid_export = np.clip(-grid_net, 0, None)
    meter_v = 400 + 2.5 * _noise(ts, spec.seed, 70)
    meter_f = 50 + 0.02 * _noise(ts, spec.seed, 71)
    out["factory_meter"] = pd.DataFrame({
        "timestamp": ts, "power_kw": np.round(load, 3), "voltage": np.round(meter_v, 2),
        "current": np.nan, "frequency": np.round(meter_f, 3), "temperature_c": np.nan, "soc_percent": np.nan,
        "raw_data": [{"source": SYNTHETIC_MARKER}] * len(ts),
    })
    out["grid_meter"] = pd.DataFrame({
        # Ingestion requires grid power >= 0, so the net sign lives in
        # the separate import/export series (what the aggregator reads).
        "timestamp": ts, "power_kw": np.round(grid_import, 3), "voltage": np.round(meter_v, 2),
        "current": np.nan, "frequency": np.round(meter_f, 3), "temperature_c": np.nan, "soc_percent": np.nan,
        "raw_data": [
            {"source": SYNTHETIC_MARKER, "import_power_kw": round(float(i), 3), "export_power_kw": round(float(e), 3)}
            for i, e in zip(grid_import, grid_export)
        ],
    })
    return out


def hourly_pv_forecast(spec: SiteSpec, day_start_utc: pd.Timestamp, hours: int = 48) -> pd.DataFrame:
    """Expected PV energy per hour, used only when the real weather-driven
    solar forecast can't be fetched. Clear-sky-ish with the same daily
    clearness process, no noise, no soiling knowledge (a forecaster
    wouldn't know about dirty panels)."""
    frames = simulate(
        SiteSpec(**{**spec.__dict__, "inverters": [
            InverterSpec(i.key, i.name, i.rated_kw, pr=i.pr) for i in spec.inverters
        ]}),
        day_start_utc, day_start_utc + pd.Timedelta(hours=hours), step="15min",
    )
    pv = sum(frames[i.key].set_index("timestamp")["power_kw"] for i in spec.inverters)
    energy = pv.resample("h").mean()  # mean kW over the hour == kWh
    return pd.DataFrame({"expected_power_kw": energy, "expected_energy_kwh": energy})
