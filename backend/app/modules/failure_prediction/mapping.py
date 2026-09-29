"""
Failure prediction: device telemetry -> the PVDAQ-shaped frame the
thesis models were trained on.

The models learned from one real ~1 kW residential-scale system
(PVDAQ system_id=10, 120 V AC) in its native units. A factory inverter
is hundreds of kW at 230/400 V, so feeding its raw numbers in would put
every input far outside the training distribution. Instead each
quantity is transferred onto the reference system's scale:

  - power (AC and DC): scaled by reference_rating / device_rating, so
    "40% of rated output" means the same thing to the model on both
  - AC voltage: per-unit against the device's nominal (nearest standard
    level), then multiplied by the reference nominal
  - DC voltage: per-unit against the window's own median (DC nominal
    isn't recorded anywhere), so the model sees variation, not level
  - currents: derived as P / V from the transferred values, keeping the
    physics self-consistent instead of scaling a third quantity
  - temperatures and irradiance: already physical units, passed through
  - anything the device doesn't report: the training median (a neutral
    value the model has seen constantly), recorded in `imputed` so the
    API can say which inputs were real

Irradiance is the one hard requirement — without it performance ratio
is meaningless and build_frame returns None. It comes from the
reading's raw_data when the device (or a site pyranometer) reports it,
else from weather GHI, which is a proxy for plane-of-array irradiance,
not the same thing — `irradiance_source` records which one was used.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.modules.failure_prediction.features import (
    AC_CURR,
    AC_VOLT,
    AMB_TEMP,
    DC_CURR,
    DC_POW,
    DC_VOLT,
    INV_TEMP,
    IRR_COL,
    MOD_TEMP1,
    MOD_TEMP2,
    POWER_COL,
    TS_COL,
)

MOD_TEMP3 = "module_temp_3__431"
DAS_TEMP = "das_temp__433"
DAS_BATT = "das_battery_voltage__434"

_STANDARD_AC_NOMINALS = [120.0, 208.0, 230.0, 240.0, 400.0, 480.0, 690.0]

# raw_data keys accepted for each optional quantity — manufacturers
# name these differently, so the first key present wins.
_RAW_KEYS = {
    "irradiance": ("poa_irradiance_w_m2", "poa_irradiance", "irradiance_w_m2", "irradiance"),
    "dc_power_kw": ("dc_power_kw",),
    "dc_voltage": ("dc_voltage", "dc_voltage_v", "pv_voltage"),
    "module_temp": ("module_temp_c", "module_temperature_c", "panel_temp_c"),
    "ambient_temp": ("ambient_temp_c", "ambient_temperature_c"),
}

# NOCT cell-temperature model: T_mod = T_amb + G * (NOCT - 20) / 800.
_NOCT_C = 45.0

# 02_preprocess.py interpolated gaps of up to 5 samples at native
# resolution; allowing 15 one-minute steps here tolerates devices that
# report every 5-10 minutes without inventing long flat stretches.
_MAX_INTERPOLATE_MINUTES = 15


@dataclass
class ReadingPoint:
    timestamp: pd.Timestamp
    power_kw: float
    voltage: float | None = None
    temperature_c: float | None = None
    raw_data: dict | None = None


@dataclass
class WeatherSample:
    timestamp: pd.Timestamp
    irradiance_w_m2: float | None
    temperature_c: float | None


@dataclass
class MappedFrame:
    frame: pd.DataFrame
    scale: float
    imputed: list[str] = field(default_factory=list)
    irradiance_source: str = "device"


def raw_value(raw: dict | None, key: str) -> float | None:
    if not raw:
        return None
    for name in _RAW_KEYS[key]:
        value = raw.get(name)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def infer_ac_nominal(voltages: pd.Series) -> float | None:
    clean = voltages.dropna()
    if clean.empty:
        return None
    median = float(clean.median())
    return min(_STANDARD_AC_NOMINALS, key=lambda n: abs(n - median))


def build_frame(
    readings: list[ReadingPoint],
    rated_kw: float,
    meta: dict,
    weather: list[WeatherSample] | None = None,
    local_tz: str = "UTC",
) -> MappedFrame | None:
    if not readings or rated_kw <= 0:
        return None

    medians = meta["training_medians"]
    ref = meta["reference"]
    scale = ref["ac_power_w"] / (rated_kw * 1000.0)

    raw = pd.DataFrame(
        {
            TS_COL: pd.to_datetime([r.timestamp for r in readings], utc=True),
            "power_kw": [r.power_kw for r in readings],
            "voltage": [r.voltage for r in readings],
            "temperature_c": [r.temperature_c for r in readings],
            **{
                key: [raw_value(r.raw_data, key) for r in readings]
                for key in _RAW_KEYS
            },
        }
    ).astype({c: float for c in ["power_kw", "voltage", "temperature_c", *_RAW_KEYS]})

    # Devices poll every few seconds; the model's features are defined
    # at one-minute resolution (then averaged to 15-minute bins).
    minute = (
        raw.set_index(TS_COL)
        .resample("1min")
        .mean()
        .interpolate(method="time", limit=_MAX_INTERPOLATE_MINUTES, limit_area="inside")
    )

    irradiance_source = "device"
    if minute["irradiance"].isna().all():
        if not weather:
            return None
        weather_df = (
            pd.DataFrame(
                {
                    TS_COL: pd.to_datetime([w.timestamp for w in weather], utc=True),
                    "irradiance": [w.irradiance_w_m2 for w in weather],
                    "weather_temp": [w.temperature_c for w in weather],
                }
            )
            .astype({"irradiance": float, "weather_temp": float})
            .set_index(TS_COL)
            .sort_index()
        )
        # Hourly weather -> minutes by time interpolation over the union
        # of both indexes, then read back at the telemetry's minutes.
        union = weather_df.index.union(minute.index)
        weather_min = weather_df.reindex(union).interpolate(method="time").reindex(minute.index)
        minute["irradiance"] = weather_min["irradiance"]
        if minute["ambient_temp"].isna().all():
            minute["ambient_temp"] = weather_min["weather_temp"]
        irradiance_source = "weather"

    minute = minute.dropna(subset=["power_kw", "irradiance"])
    # 02_preprocess.py's night filter: the models never saw a row with
    # zero output or zero irradiance.
    minute = minute[(minute["power_kw"] > 0) & (minute["irradiance"] > 0)]
    if minute.empty:
        return None

    imputed: list[str] = []
    out = pd.DataFrame(index=minute.index)

    out[POWER_COL] = minute["power_kw"] * 1000.0 * scale

    nominal = infer_ac_nominal(minute["voltage"])
    if nominal is None:
        out[AC_VOLT] = medians[AC_VOLT]
        imputed.append("ac_voltage")
    else:
        out[AC_VOLT] = (minute["voltage"] / nominal * ref["ac_voltage_v"]).fillna(medians[AC_VOLT])
    out[AC_CURR] = out[POWER_COL] / out[AC_VOLT]

    if minute["dc_power_kw"].notna().any():
        out[DC_POW] = (minute["dc_power_kw"] * 1000.0 * scale).fillna(out[POWER_COL] / ref["ac_dc_ratio"])
    else:
        out[DC_POW] = out[POWER_COL] / ref["ac_dc_ratio"]
        imputed.append("dc_power")

    if minute["dc_voltage"].notna().any():
        dc_median = float(minute["dc_voltage"].median())
        out[DC_VOLT] = (minute["dc_voltage"] / dc_median * ref["dc_voltage_v"]).fillna(ref["dc_voltage_v"])
    else:
        out[DC_VOLT] = ref["dc_voltage_v"]
        imputed.append("dc_voltage")
    out[DC_CURR] = out[DC_POW] / out[DC_VOLT]

    out[IRR_COL] = minute["irradiance"]

    if minute["ambient_temp"].notna().any():
        out[AMB_TEMP] = minute["ambient_temp"].fillna(medians[AMB_TEMP])
    else:
        out[AMB_TEMP] = medians[AMB_TEMP]
        imputed.append("ambient_temp")

    if minute["module_temp"].notna().any():
        module = minute["module_temp"]
    else:
        module = out[AMB_TEMP] + out[IRR_COL] * (_NOCT_C - 20.0) / 800.0
        imputed.append("module_temp")
    for col in (MOD_TEMP1, MOD_TEMP2, MOD_TEMP3):
        out[col] = module.fillna(medians[col])

    if minute["temperature_c"].notna().any():
        out[INV_TEMP] = minute["temperature_c"].fillna(medians[INV_TEMP])
    else:
        out[INV_TEMP] = medians[INV_TEMP]
        imputed.append("inverter_temp")

    # Data-logger housekeeping sensors on the reference site — no
    # equivalent exists on a customer device, always neutral.
    out[DAS_TEMP] = medians[DAS_TEMP]
    out[DAS_BATT] = medians[DAS_BATT]

    for col, (low, high) in meta["clip_bounds"].items():
        out[col] = out[col].clip(lower=low, upper=high)

    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out.index.name = TS_COL
    # The training timestamps were naive site-local time, so hour/
    # day_of_year features must be read in the factory's own timezone.
    out = out.reset_index()
    out[TS_COL] = out[TS_COL].dt.tz_convert(local_tz).dt.tz_localize(None)

    return MappedFrame(frame=out, scale=scale, imputed=imputed, irradiance_source=irradiance_source)
