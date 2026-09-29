"""
Failure prediction: feature engineering.

A faithful port of OYA-PROJECT/src/03_feature_engineering.py, minus the
pseudo-labeling (labels only matter at training time). The trained
models read these exact column names in this exact order, so any
change here must be mirrored in the thesis pipeline and the models
re-exported — tests/test_failure_prediction.py checks parity against
the thesis's own features.csv when it's available locally.

Input: a DataFrame of 15-minute daytime rows with the PVDAQ sensor
column names (see mapping.py for how device telemetry gets there).
"""

import numpy as np
import pandas as pd

TS_COL = "measured_on"
POWER_COL = "ac_power__423"
DC_POW = "dc_power__422"
IRR_COL = "poa_irradiance__421"
INV_TEMP = "inverter_temp__432"
MOD_TEMP1 = "module_temp_1__429"
MOD_TEMP2 = "module_temp_2__430"
AMB_TEMP = "ambient_temp__428"
AC_VOLT = "ac_voltage__426"
AC_CURR = "ac_current__427"
DC_VOLT = "dc_pos_voltage__424"
DC_CURR = "dc_pos_current__425"

# Rolling windows need this many prior rows before a row's features
# match what the model saw in training.
WARMUP_ROWS = 30


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(TS_COL).reset_index(drop=True).copy()
    ts = df[TS_COL]

    df["hour"] = ts.dt.hour
    df["minute"] = ts.dt.minute
    df["month"] = ts.dt.month
    df["day_of_year"] = ts.dt.dayofyear
    df["day_of_week"] = ts.dt.dayofweek
    df["quarter"] = ts.dt.quarter

    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    power = df[POWER_COL]
    for w in [3, 5, 10, 30]:
        roll = power.rolling(w, min_periods=1)
        df[f"p_rmean_{w}"] = roll.mean()
        df[f"p_rstd_{w}"] = roll.std().fillna(0)
        df[f"p_rmin_{w}"] = roll.min()
        df[f"p_rmax_{w}"] = roll.max()
        df[f"p_rrange_{w}"] = df[f"p_rmax_{w}"] - df[f"p_rmin_{w}"]

    for span in [5, 15]:
        df[f"p_ewm_{span}"] = power.ewm(span=span, adjust=False).mean()

    for lag in [1, 3, 6, 12]:
        df[f"p_lag_{lag}"] = power.shift(lag)
        df[f"irr_lag_{lag}"] = df[IRR_COL].shift(lag)
    df = df.bfill().fillna(0)

    power = df[POWER_COL]
    df["power_roc"] = power.diff().fillna(0)
    df["irr_roc"] = df[IRR_COL].diff().fillna(0)
    df["power_roc2"] = df["power_roc"].diff().fillna(0)
    df["power_pct_chg"] = power.pct_change().replace([np.inf, -np.inf], 0).fillna(0)

    irr_safe = df[IRR_COL].replace(0, np.nan)
    df["perf_ratio"] = power / irr_safe
    df["perf_ratio"] = df["perf_ratio"].fillna(df["perf_ratio"].median())
    df["pr_roll_med_30"] = df["perf_ratio"].rolling(30, min_periods=1).median()
    df["pr_deviation"] = (df["perf_ratio"] - df["pr_roll_med_30"]).abs()

    dc_safe = df[DC_POW].replace(0, np.nan)
    df["ac_dc_ratio"] = (power / dc_safe).clip(0, 2).fillna(1.0)
    df["inverter_loss"] = (df[DC_POW] - power).clip(0)

    df["ac_apparent_power"] = df[AC_VOLT] * df[AC_CURR].abs()
    df["dc_apparent_power"] = df[DC_VOLT] * df[DC_CURR].abs()

    mod_avg = df[[MOD_TEMP1, MOD_TEMP2]].mean(axis=1)
    df["temp_diff"] = mod_avg - df[AMB_TEMP]
    df["temp_stress"] = (mod_avg > 60).astype(int)

    df["inv_temp_roll5"] = df[INV_TEMP].rolling(5, min_periods=1).mean()
    df["inv_temp_dev"] = (df[INV_TEMP] - df["inv_temp_roll5"]).abs()

    df["power_irr_product"] = power * df[IRR_COL]
    df["power_irr_ratio_dev"] = (
        df["perf_ratio"] - df["perf_ratio"].rolling(10).mean()
    ).fillna(0)

    return df
