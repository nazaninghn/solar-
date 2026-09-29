"""
PTF (day-ahead market clearing price) forecasting.

Timing — what is known when:
  The GÖP gate closes at 12:30 on day D for all 24 hours of D+1, and
  D+1's PTF is published ~14:00 on D. So when forecasting D+1:
    - PTF is known through D 23:00 (D's prices came out on D-1).
      For target hour h of D+1, a lag of k hours is legal iff k >= h+1;
      every lag used here is a whole number of days (>= 24 h), which is
      legal for all 24 target hours.
    - KGÜP (finalised generation plans) is settled after each day's
      auction, so only D's plan is known -> used lagged 24 h.
    - The load estimation plan (LEP) for D+1 is published on D; that's
      the one same-day fundamental used, behind `use_load_plan` so its
      contribution can be measured and switched off if its publication
      time turns out to be after gate closure.
  build_features() only ever reads rows at t-24h or earlier (except
  LEP), and tests assert it.

Scale — Turkish prices trend strongly (inflation, regulated price-cap
changes). A tree model can't extrapolate a price level it never saw, so
the target and all price features are divided by `level` = the mean
PTF of the 7 days ending D; predictions are multiplied back.

Model — one XGBoost model with a multi-quantile objective (P10/P50/P90)
over all 24 hours (hour is a feature). Evaluated by rolling-origin
backtest (expanding window, retrained per test week) against the
naive baselines the literature and traders actually use: same hour
yesterday, same hour last week, and their average.
"""

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import holidays
import numpy as np
import pandas as pd
import xgboost as xgb

TR_TZ = "Europe/Istanbul"
QUANTILES = [0.1, 0.5, 0.9]
MODEL_VERSION = "ptf-xgb-quantile-v1"
BASELINE_VERSION = "ptf-baseline-weekly-daily-v1"
MIN_TRAIN_DAYS = 120

_TR_HOLIDAYS = holidays.Turkey(years=range(2015, 2036))

LAG_DAYS = [1, 2, 3, 7, 14]


def _level(ptf_local: pd.Series) -> pd.Series:
    """Mean PTF of the 7 days ending D, aligned to every hour of D+1.
    Floored at 1 TL: spring solar can clear hours at 0, never a week."""
    daily = ptf_local.resample("D").mean()
    weekly = daily.rolling(7, min_periods=5).mean().clip(lower=1.0)
    # value for day D becomes the level of D+1
    return weekly.shift(1, freq="D").reindex(ptf_local.index, method="ffill")


def build_features(frame: pd.DataFrame, use_load_plan: bool = True) -> pd.DataFrame:
    """`frame`: hourly, UTC DatetimeIndex, columns ptf (+ optional
    fundamentals). Returns one row per hour with features, `level` and
    `target` (NaN where unknown, e.g. future hours)."""
    df = frame.copy().sort_index()
    df.index = df.index.tz_convert(TR_TZ)
    # A continuous hourly grid, so shift(24) really means "24 h earlier".
    df = df.asfreq("h")

    ptf = df["ptf"]
    level = _level(ptf)
    out = pd.DataFrame(index=df.index)
    out["level"] = level
    out["target"] = ptf / level

    local = df.index
    out["hour"] = local.hour
    out["dow"] = local.dayofweek
    out["month"] = local.month
    out["is_weekend"] = (local.dayofweek >= 5).astype(int)
    dates = pd.Series(local.date, index=local)
    out["is_holiday"] = dates.map(lambda d: int(d in _TR_HOLIDAYS)).values
    out["prev_day_holiday"] = dates.map(lambda d: int((d - timedelta(days=1)) in _TR_HOLIDAYS)).values
    out["next_day_holiday"] = dates.map(lambda d: int((d + timedelta(days=1)) in _TR_HOLIDAYS)).values

    for k in LAG_DAYS:
        out[f"ptf_lag{k}d"] = ptf.shift(24 * k) / level
    out["ptf_same_hour_mean_7d"] = (
        sum(ptf.shift(24 * k) for k in range(1, 8)) / 7.0
    ) / level

    # Day-D (yesterday relative to delivery) shape statistics.
    daily = ptf.resample("D")
    for name, series in (
        ("d0_mean", daily.mean()),
        ("d0_min", daily.min()),
        ("d0_max", daily.max()),
        ("d0_std", daily.std()),
    ):
        out[name] = series.shift(1, freq="D").reindex(df.index, method="ffill") / level
    level_30 = ptf.resample("D").mean().rolling(30, min_periods=20).mean()
    out["level_ratio_7_30"] = level / level_30.shift(1, freq="D").reindex(df.index, method="ffill")

    if use_load_plan and "load_forecast_mwh" in df:
        lf = df["load_forecast_mwh"]
        out["load_forecast"] = lf
        out["load_forecast_vs_d0"] = lf / lf.shift(24)
    for col in ("dpp_total_mwh", "dpp_wind_mwh", "dpp_solar_mwh", "dpp_hydro_mwh", "dpp_natural_gas_mwh"):
        if col in df:
            out[f"{col}_lag1d"] = df[col].shift(24)
    if "dpp_total_mwh" in df and "dpp_wind_mwh" in df:
        out["renewable_share_lag1d"] = (
            (df["dpp_wind_mwh"].fillna(0) + df.get("dpp_solar_mwh", 0) + df.get("dpp_river_mwh", 0))
            / df["dpp_total_mwh"]
        ).shift(24)

    out.index = out.index.tz_convert("UTC")
    return out


def feature_columns(features: pd.DataFrame) -> list[str]:
    return [c for c in features.columns if c not in ("level", "target")]


def _xgb_model(seed: int = 42) -> xgb.XGBRegressor:
    return xgb.XGBRegressor(
        objective="reg:quantileerror",
        quantile_alpha=np.array(QUANTILES),
        n_estimators=500,
        max_depth=6,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        tree_method="hist",
        random_state=seed,
        n_jobs=-1,
    )


def _to_prices(pred_ratio: np.ndarray, level: np.ndarray, cap: float | None) -> np.ndarray:
    prices = np.sort(pred_ratio, axis=1) * level[:, None]  # sort: no quantile crossing
    return np.clip(prices, 0.0, cap if cap else np.inf)


def price_cap(ptf: pd.Series) -> float | None:
    """Proxy for the regulated maximum price (azami uzlaştırma fiyatı):
    the highest PTF seen in the last 60 days. Turkish PTF sits at the
    cap for many hours, so this tracks it closely."""
    recent = ptf.dropna()
    if recent.empty:
        return None
    recent = recent[recent.index >= recent.index.max() - pd.Timedelta(days=60)]
    return float(recent.max())


@dataclass
class TrainedModel:
    booster: xgb.XGBRegressor
    features: list[str]
    use_load_plan: bool
    cap: float | None
    trained_through: pd.Timestamp


def train(frame: pd.DataFrame, use_load_plan: bool = True, until: pd.Timestamp | None = None) -> TrainedModel:
    feats = build_features(frame, use_load_plan)
    if until is not None:
        feats = feats[feats.index < until]
    rows = feats.dropna(subset=["target", "level", "ptf_lag7d"])
    cols = feature_columns(feats)
    if rows.index.normalize().nunique() < MIN_TRAIN_DAYS:
        raise ValueError(f"Need at least {MIN_TRAIN_DAYS} days of PTF history to train")
    model = _xgb_model()
    model.fit(rows[cols], rows["target"])
    ptf = frame["ptf"]
    cap = price_cap(ptf[ptf.index < until] if until is not None else ptf)
    return TrainedModel(model, cols, use_load_plan, cap, rows.index.max())


def predict(model: TrainedModel, frame: pd.DataFrame, delivery_date: date) -> pd.DataFrame:
    """P10/P50/P90 in TL/MWh for the 24 hours of `delivery_date` (TR)."""
    idx = delivery_hours(delivery_date)
    grid = frame.reindex(frame.index.union(idx))
    feats = build_features(grid, model.use_load_plan).reindex(idx)
    if feats["level"].isna().any():
        raise ValueError("Not enough recent PTF history to forecast this date")
    ratio = model.booster.predict(feats[model.features])
    prices = _to_prices(np.asarray(ratio).reshape(len(idx), -1), feats["level"].to_numpy(), model.cap)
    return pd.DataFrame(prices, index=idx, columns=["p10", "p50", "p90"])


def delivery_hours(delivery_date: date) -> pd.DatetimeIndex:
    start = pd.Timestamp(delivery_date).tz_localize(TR_TZ)
    return pd.date_range(start, periods=24, freq="h").tz_convert("UTC")


def baseline_forecast(frame: pd.DataFrame, delivery_date: date) -> pd.DataFrame:
    """Average of same hour on D and same hour a week before delivery,
    with a P10-P90 band from the spread of the last 7 same-hour prices.
    Used whenever no trained model exists yet."""
    idx = delivery_hours(delivery_date)
    ptf = frame["ptf"].asfreq("h")
    rows = []
    for ts in idx:
        lag1 = ptf.get(ts - pd.Timedelta(hours=24))
        lag7 = ptf.get(ts - pd.Timedelta(hours=168))
        hist = [ptf.get(ts - pd.Timedelta(hours=24 * k)) for k in range(1, 8)]
        hist = [h for h in hist if h is not None and not math.isnan(h)]
        centre = np.nanmean([v for v in (lag1, lag7) if v is not None])
        if not hist or math.isnan(centre):
            raise ValueError("Not enough recent PTF history for a baseline forecast")
        rows.append((np.percentile(hist, 10), centre, np.percentile(hist, 90)))
    out = pd.DataFrame(rows, index=idx, columns=["p10", "p50", "p90"])
    out["p10"] = np.minimum(out["p10"], out["p50"])
    out["p90"] = np.maximum(out["p90"], out["p50"])
    return out


# --- Evaluation ---


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - actual
    mae = float(np.mean(np.abs(err)))
    return {
        "mae": round(mae, 2),
        "rmse": round(float(np.sqrt(np.mean(err**2))), 2),
        # MAE relative to the mean price: comparable across years
        # despite inflation, and defined when individual hours are 0.
        "rel_mae_pct": round(100 * mae / float(np.mean(np.abs(actual))), 2),
    }


def _pinball(actual: np.ndarray, pred: np.ndarray, q: float) -> float:
    diff = actual - pred
    return float(np.mean(np.maximum(q * diff, (q - 1) * diff)))


def backtest(frame: pd.DataFrame, test_weeks: int = 12, use_load_plan: bool = True) -> dict:
    """Rolling-origin: for each of the last `test_weeks` weeks, train on
    everything before that week, forecast each day of it."""
    ptf = frame["ptf"].dropna()
    last_day = ptf.index.tz_convert(TR_TZ).normalize().max()
    start = last_day - pd.Timedelta(weeks=test_weeks) + pd.Timedelta(days=1)

    records = []
    for w in range(test_weeks):
        week_start = start + pd.Timedelta(weeks=w)
        model = train(frame, use_load_plan, until=week_start.tz_convert("UTC"))
        for d in range(7):
            day = (week_start + pd.Timedelta(days=d)).date()
            if pd.Timestamp(day).tz_localize(TR_TZ) > last_day:
                break
            idx = delivery_hours(day)
            actual = ptf.reindex(idx)
            if actual.isna().any():
                continue
            # Hide every price from the delivery day on, so nothing about
            # D+1 or later can reach the features even by accident;
            # fundamentals stay (LEP for D+1 is known, KGÜP is lagged).
            masked = frame.assign(ptf=frame["ptf"].where(frame.index < idx[0]))
            q = predict(model, masked, day)
            base = baseline_forecast(frame[frame.index < idx[0]], day)
            for ts in idx:
                records.append({
                    "timestamp": ts,
                    "actual": actual[ts],
                    "model_p10": q.at[ts, "p10"], "model_p50": q.at[ts, "p50"], "model_p90": q.at[ts, "p90"],
                    "naive_d1": ptf.get(ts - pd.Timedelta(hours=24)),
                    "naive_d7": ptf.get(ts - pd.Timedelta(hours=168)),
                    "baseline": base.at[ts, "p50"],
                })

    res = pd.DataFrame(records).dropna()
    a = res["actual"].to_numpy()
    report = {
        "test_weeks": test_weeks,
        "test_hours": int(len(res)),
        "test_start": str(res["timestamp"].min()),
        "test_end": str(res["timestamp"].max()),
        "use_load_plan": use_load_plan,
        "models": {
            "xgboost_p50": _metrics(a, res["model_p50"].to_numpy()),
            "naive_same_hour_yesterday": _metrics(a, res["naive_d1"].to_numpy()),
            "naive_same_hour_last_week": _metrics(a, res["naive_d7"].to_numpy()),
            "baseline_avg_d1_d7": _metrics(a, res["baseline"].to_numpy()),
        },
        "interval": {
            "p10_p90_coverage_pct": round(100 * float(np.mean((a >= res["model_p10"]) & (a <= res["model_p90"]))), 1),
            "pinball_p10": round(_pinball(a, res["model_p10"].to_numpy(), 0.1), 2),
            "pinball_p50": round(_pinball(a, res["model_p50"].to_numpy(), 0.5), 2),
            "pinball_p90": round(_pinball(a, res["model_p90"].to_numpy(), 0.9), 2),
        },
    }
    best_naive = min(
        report["models"][k]["mae"]
        for k in ("naive_same_hour_yesterday", "naive_same_hour_last_week", "baseline_avg_d1_d7")
    )
    report["skill_vs_best_naive_pct"] = round(100 * (1 - report["models"]["xgboost_p50"]["mae"] / best_naive), 1)
    return report


# --- Persistence ---


def save(model: TrainedModel, directory: Path, report: dict | None = None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    model.booster.save_model(directory / "ptf_xgb.json")
    meta = {
        "version": MODEL_VERSION,
        "features": model.features,
        "use_load_plan": model.use_load_plan,
        "cap": model.cap,
        "trained_through": model.trained_through.isoformat(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "quantiles": QUANTILES,
        "backtest": report,
    }
    (directory / "ptf_meta.json").write_text(json.dumps(meta, indent=2))


def load(directory: Path) -> tuple[TrainedModel, dict] | None:
    meta_path = directory / "ptf_meta.json"
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text())
    booster = _xgb_model()
    booster.load_model(directory / "ptf_xgb.json")
    model = TrainedModel(
        booster, meta["features"], meta["use_load_plan"], meta["cap"], pd.Timestamp(meta["trained_through"])
    )
    return model, meta
