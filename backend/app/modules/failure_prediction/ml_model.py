"""
Failure prediction: the trained PV models from the OYA-PROJECT thesis.

Two XGBoost boosters, loaded once from portable JSON (never pickles —
see scripts/export_failure_models.py):

  - binary: P(a daylight fault occurs within the next 180 minutes, same
    day), from OYA-PROJECT/src/15_retrain_timeaware.py, rule-derived
    features excluded so it predicts ahead instead of re-detecting the
    rules. Held-out days: ROC-AUC 0.758, AP 0.489, F1 0.431 (precision
    0.38) vs 0.716 / 0.388 / 0.375 for the best clock+persistence
    baseline; 58% of fault onsets flagged, mean lead 143 min. That's a
    real but modest signal — it's one weighted input to the risk score
    (scoring.py), never an alarm on its own.
  - fault_type: which fault family the current behaviour looks like —
    diagnosis of the present, not forecasting (daylight macro-F1 0.74).

Both were trained on daylight rows only (POA >= 150 W/m^2), so only
daylight bins are scored; at night/dusk predict() returns None.

Both expect features built at one-minute resolution and averaged into
15-minute bins (verified bit-for-bit against the thesis's features.csv;
see tests/test_failure_prediction.py).
"""

import json
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from app.modules.failure_prediction.features import TS_COL, WARMUP_ROWS, build_features

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

# How many 15-minute bins of history must exist before a prediction is
# made — WARMUP_ROWS one-minute rows cover the longest rolling window;
# two full bins on top means the newest bin isn't mostly warm-up.
MIN_BINS = 2
BIN = "15min"


@dataclass
class MLPrediction:
    failure_probability: float
    threshold: float
    alarm: bool
    horizon_minutes: int
    fault_type: str | None
    fault_type_confidence: float | None
    probability_series: list[tuple[pd.Timestamp, float]]
    model_version: str


class PVFailureModel:
    def __init__(self, artifact_dir: Path = ARTIFACT_DIR):
        self.meta = json.loads((artifact_dir / "model_meta.json").read_text())

        self._binary = xgb.Booster()
        self._binary.load_model(artifact_dir / self.meta["binary"]["file"])
        self._fault_type = xgb.Booster()
        self._fault_type.load_model(artifact_dir / self.meta["fault_type"]["file"])

    @property
    def threshold(self) -> float:
        return self.meta["binary"]["threshold"]

    @property
    def horizon_minutes(self) -> int:
        return self.meta["binary"]["horizon_minutes"]

    def binned_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        minute_features = build_features(frame).iloc[WARMUP_ROWS:]
        return (
            minute_features.set_index(TS_COL)
            .resample(BIN)
            .mean()
            .dropna(subset=["ac_power__423"])
        )

    @property
    def daylight_irradiance(self) -> float:
        return self.meta["binary"]["daylight_irradiance_w_m2"]

    def predict(self, frame: pd.DataFrame) -> MLPrediction | None:
        if len(frame) <= WARMUP_ROWS:
            return None
        bins = self.binned_features(frame)
        bins = bins[bins["poa_irradiance__421"] >= self.daylight_irradiance]
        if len(bins) < MIN_BINS:
            return None

        binary_cols = self.meta["binary"]["features"]
        probs = self._binary.predict(
            xgb.DMatrix(bins[binary_cols].to_numpy(dtype=np.float32))
        )

        fault_cols = self.meta["fault_type"]["features"]
        latest = bins[fault_cols].iloc[[-1]].to_numpy(dtype=np.float32)
        # Softmax over raw margins rather than predict()'s output, so
        # this works whether the booster was saved as multi:softprob or
        # multi:softmax (which returns only the class index).
        margins = self._fault_type.predict(xgb.DMatrix(latest), output_margin=True)[0]
        exp = np.exp(margins - margins.max())
        class_probs = exp / exp.sum()
        best = int(np.argmax(class_probs))
        fault_class = self.meta["fault_type"]["classes"][best]
        fault_name = self.meta["fault_type"]["fault_names"][str(fault_class)]

        probability = float(probs[-1])
        return MLPrediction(
            failure_probability=round(probability, 4),
            threshold=self.threshold,
            alarm=probability >= self.threshold,
            horizon_minutes=self.horizon_minutes,
            fault_type=None if fault_class == 0 else fault_name,
            fault_type_confidence=round(float(class_probs[best]), 4),
            probability_series=[
                (ts, round(float(p), 4)) for ts, p in zip(bins.index, probs)
            ],
            model_version=self.meta["binary"]["version"],
        )


_model: PVFailureModel | None = None
_lock = threading.Lock()


def get_model() -> PVFailureModel:
    """Lazy singleton — ~3 MB of trees, loaded on first use, not import."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = PVFailureModel()
    return _model
