# PTF Forecast Evaluation

The source of the only accuracy figure the product publishes (landing
page "Forecast Energy" card and FAQ): **mean absolute error of 14.6% of
the average price on 12 held-out weeks, 16% below the best naive
benchmark**. Any change to that copy must come from a re-run of the
evaluation below, and this file must be updated with it.

Solar-generation and consumption forecast accuracy are **not measured
yet** (no real facility telemetry exists), so no figure is published
for them.

## What is forecast

The Turkish day-ahead market clearing price (PTF, TL/MWh) for all 24
hours of day D+1, issued on day D before the 12:30 GÖP gate closure.
Model: `ptf-xgb-quantile-v1` (`app/modules/market/forecasting.py`), an
XGBoost multi-quantile regressor (P10/P50/P90). The P50 is what the
error metrics score.

## Dataset

| | |
|---|---|
| Source | EPİAŞ Transparency Platform, `/v1/markets/dam/data/mcp` (real published PTF) |
| History in DB | 26,448 hourly prices, 2023-09-25 00:00 → 2026-09-30 23:00 (Turkey time) |
| Test period | 2026-07-09 00:00 → 2026-09-30 23:00 (Turkey time), 12 weeks |
| Test size | 2,016 hours (84 delivery days × 24) |
| Trained through (shipped model) | 2026-09-30 23:00 (Turkey time) |

## Protocol

- **Rolling origin, expanding window:** for each of the 12 test weeks,
  the model is retrained on all history strictly before that week,
  then forecasts each day of the week.
- **Information cut-off:** every price from the delivery day onward is
  masked before features are built, so a forecast uses only what a
  bidder has at gate closure. Only whole-day lags (≥ 24 h) of price
  are features; KGÜP generation plans are lagged 24 h (they're
  finalised after each day's auction). `tests/test_market.py::
  test_features_never_see_the_delivery_day` asserts that altering
  delivery-day prices can't change the forecast.
- **Variants:** with and without TEİAŞ's next-day load estimation plan
  as a feature. The shipped model is whichever has the lower test MAE.

## Metrics

- **MAE** = mean over test hours of |P50 − actual PTF|, in TL/MWh.
- **Relative MAE** = MAE ÷ mean |actual PTF| over the same hours × 100.
  This is the "14.6% of the average price" figure. Relative to the
  mean price rather than a per-hour MAPE, because PTF clears at or
  near 0 TL in some spring/solar hours, where MAPE is undefined.
- **Skill vs best naive** = 1 − MAE(model) ÷ MAE(best naive baseline).
- **P10–P90 coverage** = share of test hours whose actual price fell
  inside the forecast P10–P90 band (target 80%).

## Results

| Method | MAE (TL/MWh) | RMSE (TL/MWh) | Relative MAE |
|---|---:|---:|---:|
| **XGBoost P50 (shipped, no load plan)** | **408.2** | **550.5** | **14.6%** |
| XGBoost P50 with load plan feature | 409.5 | — | 14.7% |
| Average of same hour yesterday and last week | 487.5 | 654.0 | 17.4% |
| Same hour yesterday | 579.3 | 833.1 | 20.7% |
| Same hour last week | 590.9 | 790.1 | 21.2% |

- Skill vs best naive (the average baseline): **16.3%**
- P10–P90 coverage: **79.1%** (target 80%)
- Pinball loss P10 / P50 / P90: 94.4 / 204.1 / 89.8
- The load estimation plan didn't improve accuracy (409.5 vs 408.2),
  so the shipped model doesn't use it.

## Reproduce

```bash
cd backend
python scripts/train_ptf_model.py --backfill-days 1100 --test-weeks 12
```

Needs `EPIAS_USERNAME` / `EPIAS_PASSWORD` in `backend/.env`. Writes the
model and this same backtest report to `var/models/ptf/ptf_meta.json`
(gitignored; data-dependent). The weekly retrain job
(`app/jobs/market_jobs.py`) re-runs an 8-week backtest on every
retrain; published figures should only change from a deliberate
12-week re-run recorded here.

## Limitations

- One 12-week window (summer–early autumn 2026). Seasonal behaviour
  (spring solar-driven zero-price hours, winter gas constraints) isn't
  covered; accuracy in other seasons may differ.
- Prices are strongly regime-dependent (regulated price cap,
  inflation). The model normalises by the trailing 7-day mean price,
  but an abrupt cap change can still cause errors until retraining.
- The evaluation scores forecasts only; it does not measure the
  revenue of the sell offers built from them.
