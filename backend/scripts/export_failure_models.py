"""
Failure prediction: export the trained PV predictive-maintenance models
from the OYA-PROJECT thesis pipeline into this backend.

Source: OYA-PROJECT/src/15_retrain_timeaware.py (PVDAQ system_id=10,
real field data). That script — not the older 10_retrain_clean.py — is
used on purpose: 10_retrain_clean's "3h ahead" label counted 12 *rows*
ahead across the removed night gap and treated dusk low-light as
faults, so its model mostly learned time of day (a clock-only baseline
scored AUC 0.86 on it). 15_retrain_timeaware uses a same-day 180-minute
horizon on daylight rows only.

    app/modules/failure_prediction/artifacts/
        pv_failure_binary.json   <- xgb_timeaware.json (daylight fault within 3h)
        pv_fault_type.json       <- xgb_faulttype_daylight.json (diagnosis)
        model_meta.json          <- feature order, threshold, class map,
                                    training medians, clip bounds,
                                    reference rating, test metrics

Everything is JSON on both ends — nothing is unpickled.

Usage:
    python scripts/export_failure_models.py --oya-dir "D:/OYA-PROJECT"
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ARTIFACT_DIR = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "modules"
    / "failure_prediction"
    / "artifacts"
)

# Sensor columns whose training-set medians are used as a neutral fill
# when a live device doesn't report that quantity.
SENSOR_COLUMNS = [
    "ac_current__427",
    "ac_power__423",
    "ac_voltage__426",
    "ambient_temp__428",
    "das_temp__433",
    "dc_pos_current__425",
    "dc_pos_voltage__424",
    "dc_power__422",
    "inverter_temp__432",
    "module_temp_1__429",
    "module_temp_2__430",
    "module_temp_3__431",
    "poa_irradiance__421",
    "das_battery_voltage__434",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oya-dir", required=True, type=Path)
    args = parser.parse_args()

    models_dir = args.oya_dir / "models"
    processed_dir = args.oya_dir / "data" / "processed"

    binary_meta = json.loads((models_dir / "xgb_timeaware_meta.json").read_text())
    fault_meta = json.loads((models_dir / "xgb_faulttype_daylight_meta.json").read_text())

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(models_dir / "xgb_timeaware.json", ARTIFACT_DIR / "pv_failure_binary.json")
    shutil.copyfile(models_dir / "xgb_faulttype_daylight.json", ARTIFACT_DIR / "pv_fault_type.json")

    clean = pd.read_csv(processed_dir / "merged_clean.csv", usecols=SENSOR_COLUMNS)
    medians = {col: round(float(clean[col].median()), 4) for col in SENSOR_COLUMNS}
    # 02_preprocess.py clipped every sensor to its 1st-99th percentile
    # before training, so merged_clean's min/max *are* those bounds —
    # live inputs get the same clip so nothing reaches the model outside
    # the range it was trained on.
    clip_bounds = {
        col: [round(float(clean[col].min()), 4), round(float(clean[col].max()), 4)]
        for col in SENSOR_COLUMNS
    }
    # The training system's rating, taken as the 99.5th percentile of AC
    # output rather than the max so a single clipped spike doesn't set it.
    reference_ac_w = round(float(clean["ac_power__423"].quantile(0.995)), 1)

    metrics = binary_meta["test_metrics"]
    meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": "OYA-PROJECT/src/15_retrain_timeaware.py (PVDAQ system_id=10)",
        "binary": {
            "file": "pv_failure_binary.json",
            "version": "pv-failure-xgb-timeaware-v1",
            "features": binary_meta["features"],
            "threshold": binary_meta["threshold"],
            "horizon_minutes": binary_meta["horizon_minutes"],
            "daylight_irradiance_w_m2": binary_meta["daylight_irradiance_w_m2"],
            "label": binary_meta["label"],
            "test_metrics": {
                "precision": metrics["Precision"],
                "recall": metrics["Recall"],
                "f1": metrics["F1"],
                "roc_auc": metrics["ROC_AUC"],
                "average_precision": metrics["AP"],
                "mcc": metrics["MCC"],
            },
            "lead_time": binary_meta["lead_time"],
        },
        "fault_type": {
            "file": "pv_fault_type.json",
            "version": "pv-fault-type-xgb-daylight-v1",
            "features": fault_meta["features"],
            # Booster output index i corresponds to classes[i].
            "classes": fault_meta["classes"],
            "fault_names": fault_meta["fault_names"],
            "test_macro_f1": fault_meta["test_macro_f1"],
        },
        "reference": {
            "ac_power_w": reference_ac_w,
            "ac_voltage_v": medians["ac_voltage__426"],
            "dc_voltage_v": medians["dc_pos_voltage__424"],
            "ac_dc_ratio": round(medians["ac_power__423"] / medians["dc_power__422"], 4),
        },
        "training_medians": medians,
        "clip_bounds": clip_bounds,
    }

    (ARTIFACT_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"Exported artifacts to {ARTIFACT_DIR}")
    print(f"  reference AC rating: {reference_ac_w} W")
    print(f"  binary threshold: {meta['binary']['threshold']:.4f}")


if __name__ == "__main__":
    main()
