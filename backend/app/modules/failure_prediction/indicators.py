"""
Failure prediction: rule-based degradation and fault indicators.

These cover what the ML model can't: equipment other than PV inverters
(batteries, meters), communications, and slow degradation measured in
days or weeks rather than the model's 3-hour horizon. Each indicator is
a physical quantity with a documented threshold, scored 0-100, so a
risk score can always be traced back to "which measurement, what value,
compared against what".

Thresholds are engineering defaults (IEC 61724 performance-ratio
practice, typical Li-ion datasheet limits, EN 50160 voltage/frequency
bands), not fitted — they're the obvious thing to calibrate once
FailureEvent rows accumulate real outcomes.

Every function takes plain data (a DataFrame of readings, ORM objects
for static specs) and never touches the DB, so all of it is unit
testable without Postgres.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass
class Indicator:
    code: str
    category: str
    label: str
    value: float | None
    unit: str
    threshold: float | None
    score: float
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _ramp(value: float, start: float, end: float, max_score: float = 90.0) -> float:
    """0 at `start`, max_score at `end`, linear between; works for
    rising (start < end) and falling (start > end) bad directions."""
    if start == end:
        return 0.0
    frac = (value - start) / (end - start)
    return round(float(np.clip(frac, 0.0, 1.0) * max_score), 1)


# --- PV inverter / array ---

PR_WARN = 0.75
PR_CRITICAL = 0.50
DAYLIGHT_FOR_PR_W_M2 = 200.0
TRIP_IRRADIANCE_W_M2 = 300.0
INVERTER_TEMP_WARN_C = 65.0
INVERTER_TEMP_CRITICAL_C = 80.0
VOLTAGE_BAND_PU = 0.10
FREQUENCY_BAND_HZ = 0.5


def performance_ratio(df: pd.DataFrame, rated_kw: float) -> float | None:
    """IEC 61724-style PR over the window: energy delivered divided by
    energy the rated array would deliver at the measured irradiance.
    Only minutes with enough light count — at low irradiance PR is
    dominated by noise and inverter start-up losses."""
    if rated_kw <= 0 or "irradiance" not in df or df["irradiance"].isna().all():
        return None
    lit = df[df["irradiance"] >= DAYLIGHT_FOR_PR_W_M2]
    if len(lit) < 30:
        return None
    expected = (rated_kw * lit["irradiance"] / 1000.0).sum()
    if expected <= 0:
        return None
    return float(lit["power_kw"].sum() / expected)


def inverter_indicators(df: pd.DataFrame, rated_kw: float) -> list[Indicator]:
    """`df` is one-minute rows: power_kw, voltage, frequency,
    temperature_c, irradiance (any may be NaN)."""
    out: list[Indicator] = []
    if df.empty:
        return out

    pr = performance_ratio(df, rated_kw)
    if pr is not None:
        out.append(Indicator(
            "performance_ratio", "PV_ARRAY", "Performance ratio",
            round(pr, 3), "ratio", PR_WARN,
            _ramp(pr, PR_WARN, PR_CRITICAL),
            f"Array delivered {pr:.0%} of the energy expected for the measured irradiance.",
        ))

    if rated_kw > 0 and "irradiance" in df and df["irradiance"].notna().any():
        bright = df[df["irradiance"] >= TRIP_IRRADIANCE_W_M2]
        if len(bright) >= 30:
            tripped = float((bright["power_kw"] < 0.01 * rated_kw).mean())
            out.append(Indicator(
                "daylight_trips", "INVERTER", "Zero output in daylight",
                round(tripped * 100, 1), "%", 2.0,
                _ramp(tripped * 100, 2.0, 20.0),
                f"Output was ~0 for {tripped:.0%} of bright-sky minutes (inverter trips or string disconnects).",
            ))

    temp = df["temperature_c"].dropna()
    if not temp.empty:
        # 15-minute mean, not the single hottest sample — one noisy
        # reading shouldn't read as thermal stress.
        peak = float(temp.rolling(15, min_periods=5).mean().max())
        if not np.isnan(peak):
            out.append(Indicator(
                "inverter_temperature", "INVERTER", "Inverter temperature",
                round(peak, 1), "°C", INVERTER_TEMP_WARN_C,
                _ramp(peak, INVERTER_TEMP_WARN_C, INVERTER_TEMP_CRITICAL_C),
                f"Peak 15-minute inverter temperature {peak:.1f} °C.",
            ))

    out.extend(_power_quality(df, "INVERTER"))
    return out


def _power_quality(df: pd.DataFrame, category: str) -> list[Indicator]:
    from app.modules.failure_prediction.mapping import infer_ac_nominal

    out: list[Indicator] = []
    voltage = df["voltage"].dropna()
    nominal = infer_ac_nominal(voltage)
    if nominal:
        outside = float(((voltage / nominal - 1).abs() > VOLTAGE_BAND_PU).mean())
        out.append(Indicator(
            "voltage_deviation", category, "AC voltage outside ±10%",
            round(outside * 100, 2), "%", 1.0,
            _ramp(outside * 100, 1.0, 10.0),
            f"{outside:.1%} of samples outside ±10% of {nominal:.0f} V nominal.",
        ))

    freq = df["frequency"].dropna()
    if not freq.empty:
        nominal_f = 60.0 if abs(freq.median() - 60) < abs(freq.median() - 50) else 50.0
        outside = float(((freq - nominal_f).abs() > FREQUENCY_BAND_HZ).mean())
        out.append(Indicator(
            "frequency_deviation", category, "Frequency outside ±0.5 Hz",
            round(outside * 100, 2), "%", 1.0,
            _ramp(outside * 100, 1.0, 10.0),
            f"{outside:.1%} of samples outside {nominal_f:.0f} ±0.5 Hz.",
        ))
    return out


def meter_indicators(df: pd.DataFrame) -> list[Indicator]:
    return _power_quality(df, "METER") if not df.empty else []


# --- Battery ---

SOH_WARN = 85.0
SOH_CRITICAL = 70.0
BATTERY_TEMP_WARN_C = 40.0
BATTERY_TEMP_CRITICAL_C = 55.0
EFFICIENCY_WARN = 90.0
EFFICIENCY_CRITICAL = 75.0
# Typical LFP datasheet rating; used only when nothing more specific exists.
RATED_CYCLES = 6000


def battery_indicators(df: pd.DataFrame, battery) -> list[Indicator]:
    """`battery` is the factory's BatterySystem (or None)."""
    out: list[Indicator] = []

    soh = getattr(battery, "state_of_health_percent", None)
    if soh is not None:
        out.append(Indicator(
            "state_of_health", "BATTERY", "State of health",
            round(soh, 1), "%", SOH_WARN, _ramp(soh, SOH_WARN, SOH_CRITICAL),
            f"Battery holds {soh:.0f}% of its original capacity (end-of-life is usually 70-80%).",
        ))

    temps = df["temperature_c"].dropna() if not df.empty else pd.Series(dtype=float)
    temp = float(temps.max()) if not temps.empty else getattr(battery, "temperature_c", None)
    if temp is not None:
        score = _ramp(temp, BATTERY_TEMP_WARN_C, BATTERY_TEMP_CRITICAL_C)
        if temp < 0:
            score = max(score, 50.0)
        out.append(Indicator(
            "battery_temperature", "BATTERY", "Battery temperature",
            round(temp, 1), "°C", BATTERY_TEMP_WARN_C, score,
            f"Max cell/pack temperature {temp:.1f} °C.",
        ))

    efficiency = getattr(battery, "efficiency_percent", None)
    if efficiency is not None:
        out.append(Indicator(
            "round_trip_efficiency", "BATTERY", "Round-trip efficiency",
            round(efficiency, 1), "%", EFFICIENCY_WARN,
            _ramp(efficiency, EFFICIENCY_WARN, EFFICIENCY_CRITICAL, 80.0),
            f"Round-trip efficiency {efficiency:.0f}%.",
        ))

    cycles = getattr(battery, "cycle_count", None)
    if cycles:
        used = cycles / RATED_CYCLES
        out.append(Indicator(
            "cycle_wear", "BATTERY", "Cycle life used",
            round(used * 100, 1), "%", 70.0, _ramp(used * 100, 70.0, 100.0, 80.0),
            f"{cycles} of ~{RATED_CYCLES} rated cycles used.",
        ))

    if not df.empty and df["soc_percent"].notna().any():
        min_soc = getattr(battery, "min_soc_percent", None) or 10.0
        soc = df["soc_percent"].dropna()
        deep = float((soc < min_soc).mean())
        out.append(Indicator(
            "deep_discharge", "BATTERY", "Time below minimum SOC",
            round(deep * 100, 1), "%", 5.0, _ramp(deep * 100, 5.0, 30.0, 70.0),
            f"{deep:.0%} of the window below the {min_soc:.0f}% SOC floor (accelerates wear).",
        ))

        moving = df["power_kw"].abs() > 1.0
        if moving.sum() >= 30 and float(df.loc[moving, "soc_percent"].std()) < 0.1:
            out.append(Indicator(
                "soc_flatline", "BATTERY", "SOC not changing under load",
                0.0, "σ %", 0.1, 60.0,
                "SOC stayed flat while the battery was charging/discharging — BMS or sensor fault.",
            ))
    return out


# --- Communications (every device type) ---

GAP_MINUTES = 15


def comms_indicators(
    device, timestamps: pd.Series, qualities: pd.Series, window_hours: float
) -> list[Indicator]:
    out: list[Indicator] = []

    errors = device.consecutive_error_count or 0
    out.append(Indicator(
        "consecutive_errors", "COMMS", "Consecutive poll failures",
        float(errors), "polls", 3.0, _ramp(errors, 0, 5),
        f"{errors} consecutive failed polls"
        + (f" — last error: {device.last_error_message}" if device.last_error_message else "."),
    ))

    if device.status == "OFFLINE":
        out.append(Indicator(
            "offline", "COMMS", "Device offline", 1.0, "", None, 90.0,
            "Device has stopped reporting data.",
        ))

    if len(timestamps) >= 2:
        ts = pd.to_datetime(timestamps, utc=True).sort_values()
        gaps = ts.diff().dt.total_seconds().div(60).dropna()
        long_gaps = gaps[gaps > GAP_MINUTES]
        missing_min = float(long_gaps.sum())
        out.append(Indicator(
            "data_gaps", "COMMS", "Data gaps > 15 min",
            float(len(long_gaps)), "gaps", 1.0, min(90.0, 15.0 * len(long_gaps)),
            f"{len(long_gaps)} gaps totalling {missing_min:.0f} min in the last {window_hours:.0f} h.",
        ))
    elif device.is_active:
        out.append(Indicator(
            "no_data", "COMMS", "No telemetry in window", 0.0, "readings", None, 70.0,
            f"No readings received in the last {window_hours:.0f} h.",
        ))

    if len(qualities):
        bad = float(qualities.isin(["INVALID", "SUSPECT"]).mean())
        out.append(Indicator(
            "data_quality", "COMMS", "Invalid/suspect readings",
            round(bad * 100, 2), "%", 2.0, _ramp(bad * 100, 2.0, 20.0),
            f"{bad:.1%} of readings failed validation.",
        ))
    return out


# --- Trends from assessment history ---


def days_to_threshold(
    history: list[tuple[pd.Timestamp, float]], threshold: float, min_days: float = 3.0
) -> float | None:
    """Linear trend of a degrading quantity (PR, SOH) projected forward
    to `threshold`. None unless there's >= min_days of history and the
    trend is actually heading toward the threshold."""
    if len(history) < 5:
        return None
    ts = pd.to_datetime([t for t, _ in history], utc=True)
    span_days = (ts.max() - ts.min()).total_seconds() / 86400
    if span_days < min_days:
        return None
    x = (ts - ts.min()).total_seconds().to_numpy() / 86400
    y = np.array([v for _, v in history], dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    current = slope * x.max() + intercept
    if current <= threshold:
        return 0.0
    if slope >= 0:
        return None
    return round(float((threshold - current) / slope), 1)
