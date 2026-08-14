# AI/ML Readiness Assessment (STEP 81)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## The Honest Starting Point

Every feature this product markets as "AI-powered" — recommendations, forecasting,
anomaly detection — is **rule-based or statistical, not a trained ML model**:

| Feature | What it actually is |
|---|---|
| Recommendation engine (`app/modules/recommendations/engine.py`) | If/else rules on SOC%/price/forecast thresholds + a hand-weighted 0-100 score (40% economic, 25% confidence, 20% energy impact, 15% urgency) |
| Forecasting (`app/modules/forecasting/models_ml/`) | Historical hourly average + a linear weather/day-of-week adjustment — literally named "baseline," not a placeholder name for something else |
| Anomaly detection (`app/modules/observability/anomaly_detection.py`, Step 77) | Statistical process control: flag if a value is >2.5 standard deviations from a 30-day rolling mean |

This is a **deliberate, already-documented MVP decision** (`docs/ROADMAP_V2.md` lists
"ML-based forecast models (replace baseline)" as future work) — not something Step 81
should quietly "correct." Nothing has been trained; no `.pkl`/`.joblib`/`.onnx` file
exists anywhere in this codebase; `requirements.txt` has no numpy, pandas, or
scikit-learn.

## Data Readiness (real, computed — not estimated)

`GET /api/v1/ai-readiness/data-readiness` — real per-factory day-span and sample
count from `energy_daily`. As of this assessment: **85 factories have some history,
zero have reached the 90-day floor** this doc treats as the minimum worth training
a baseline-comparison model against (see `app/modules/ai_readiness/data_readiness.py`
for the exact thresholds and their reasoning). This number will change as real
customer usage accumulates — it is deliberately a live query, not a static figure
in this document.

## Genuine Future AI/ML Use Cases

Ranked by how directly they'd improve on what exists today, *conditional on* real
data volume catching up to the thresholds above:

1. **Solar generation forecasting via regression** — the most natural first model:
   `SolarBaselineModel` already isolates the prediction interface
   (`app/modules/forecasting/models_ml/base.py`'s `BaseForecastModel`), so a real
   regression model could be dropped in as a `SHADOW`-status registry entry and
   compared against the baseline via the *already-existing* `ForecastAccuracy`
   tracking — no new infrastructure needed, just a model and enough data.
2. **Battery degradation prediction** — `BatterySystem.state_of_health_percent`
   exists but nothing predicts its trajectory; a real candidate once enough
   `DeviceEnergyReading` history exists per battery.
3. **Anomaly detection upgrade** (isolation forest / seasonal decomposition) — only
   worth it once the current 2.5σ statistical approach demonstrably produces too
   many false positives/negatives in production; no evidence of that yet.
4. **Recommendation confidence via a real model** — replacing the hand-weighted
   0.4/0.3/0.3 formula with something fitted to actual accept/reject outcomes
   (`RecommendationAuditLog` already records every decision) — the lowest-priority
   item since the current formula's stated purpose (a defensible, explainable
   ranking) doesn't obviously need a black-box replacement.

None of these are built as part of Step 81, per the explicit "readiness only, no
new ML dependencies" scope decision for this step.

## Feature Engineering

No feature engineering pipeline exists — nothing to build one FOR yet, since there's
no model consuming engineered features. The raw ingredients already exist and are
real: `energy_daily` (solar/consumption/grid/battery), `electricity_prices`,
weather data via `app.weather`. When use case #1 above becomes viable, the features
are already sitting in normalized tables, not something that needs a new ETL layer.

## Model Evaluation & Lifecycle (real infrastructure, now populated)

`ForecastModelRegistry` (Step 35) already defines a real lifecycle vocabulary —
`TRAINING → VALIDATION → SHADOW → PRODUCTION → RETIRED` — but had never had a row
written to it. `app/modules/ai_readiness/model_governance.py` now seeds it with the
two models actually running today (`solar-baseline-v1`, `load-baseline-v1`),
scored against real `ForecastAccuracy` history, refreshed daily
(`app/jobs/ai_readiness_jobs.py`). A future real model would enter at `SHADOW`,
get promoted to `PRODUCTION` only once its real MAE/RMSE beats the baseline's real
MAE/RMSE in this same table — the comparison mechanism already exists.

## Model Monitoring (real, not aspirational)

`GET /api/v1/ai-readiness/drift` compares the last 14 days of forecast MAE against
the prior 14 days, per forecast type, flagging >=25% degradation. Runs daily,
opens a `MonitoringIncident` (same reuse pattern as Steps 78-80's alerts) on
breach. Requires >=10 samples in each window before evaluating — a model with 3
data points swinging 40% is noise, not drift.

## MLOps

**Not built.** There's no training pipeline, no experiment tracking, no CI
integration for model retraining, because there's no model being trained. Building
MLOps tooling for a training pipeline that doesn't exist would be speculative
infrastructure — exactly the kind of premature abstraction this project's own
engineering conventions warn against. Revisit once use case #1 is actually being
built.

## AI Cost Management

**N/A, documented decision** (same treatment as Step 80's CAC) — there is no paid
AI/ML API usage anywhere in this system: no OpenAI/Anthropic/cloud-ML calls, no
GPU compute, no inference cost. The only "AI cost" that exists is engineering time.
Revisit if a real model with real training/inference cost is ever shipped.

## Human-in-the-Loop (already fully real, not new)

Every automated decision in this system already requires human approval before it
affects anything:
- Recommendations: `accept_recommendation`/`reject_recommendation`
  (`app/modules/recommendations/service.py`), logged to `RecommendationAuditLog`
- Control actions: the full `EnergyAction` approval workflow (Step 32) — nothing
  executes against real equipment without an approval step and a safety check

## Output Validation (already fully real, not new)

- `check_recommendation_safety()` (`app/modules/recommendations/service.py`) —
  blocks confident-looking recommendations from broken/stale data sources
- `run_safety_checks()` (`app/control/safety.py`) — pre-execution validation:
  device online, SOC bounds, power limits, temperature, data freshness

Both existed before Step 81; this document just names them as what they actually
are — the output-validation layer this step's brief asks for.

## AI Security

**No LLM integration exists** — zero prompt-injection surface, confirmed by grep
across the entire codebase for any LLM/prompt-related code. The closest real
security-relevant concern for a rule-based automated-decision system is **garbage
input driving a confident wrong output** — already covered by the data-quality
gating above (Step 29/31/32's existing safety checks) and by `data_quality` flags
on ingested telemetry (Step 31: `GOOD`/`SUSPECT`/`INVALID`). If an LLM integration
is ever added, this section needs a real rewrite (prompt injection, data
exfiltration via generated output, etc.) — not before.

## Summary

| Checklist Item | Status |
|---|---|
| AI/ML use cases identified | ✅ documented above, ranked, tied to real data-readiness numbers |
| Data readiness | ✅ real per-factory computation, `GET /api/v1/ai-readiness/data-readiness` |
| Feature engineering | N/A — no model to build features for yet |
| Model evaluation | ✅ real, via existing ForecastAccuracy + newly-populated ForecastModelRegistry |
| Model lifecycle | ✅ vocabulary existed, now actually used |
| MLOps | Not built — no training pipeline exists to operate |
| Model monitoring | ✅ real drift detection, daily job, real alerts |
| AI cost management | N/A, documented — no paid AI/ML usage exists |
| Human-in-the-loop | ✅ already real (Steps 20, 29, 32) |
| Output validation | ✅ already real (Steps 29, 31, 32) |
| AI security | N/A for prompt injection (no LLM) — real concern covered by existing data-quality gating |
