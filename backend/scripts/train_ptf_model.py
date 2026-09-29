"""
Backfill EPİAŞ history, backtest and train the PTF forecaster.

    python scripts/train_ptf_model.py --backfill-days 1100 --test-weeks 12

Steps:
  1. (optional) pull --backfill-days of PTF/SMF/load plan/KGÜP into the DB
  2. rolling-origin backtest over the last --test-weeks weeks, with and
     without the next-day load plan feature, against naive baselines
  3. train on all history and save to PTF_MODEL_DIR (var/models/ptf)

Every number printed comes from real EPİAŞ data in the local DB.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal  # noqa: E402
from app.modules.market import epias_client, forecasting, service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill-days", type=int, default=0)
    parser.add_argument("--test-weeks", type=int, default=12)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.backfill_days:
            if not epias_client.is_configured():
                sys.exit("EPIAS_USERNAME / EPIAS_PASSWORD missing in backend/.env")
            today = pd.Timestamp.now(tz=forecasting.TR_TZ).normalize()
            start = (today - pd.Timedelta(days=args.backfill_days)).tz_convert("UTC").to_pydatetime()
            end = (today + pd.Timedelta(days=2)).tz_convert("UTC").to_pydatetime()
            print(f"Backfilling {args.backfill_days} days from EPİAŞ ...")
            result = asyncio.run(service.sync_market(db, start, end))
            print(json.dumps(result, indent=2, default=str))

        frame = service.load_frame(db)
        ptf = frame["ptf"].dropna() if not frame.empty else pd.Series(dtype=float)
        print(f"\nPTF history: {len(ptf):,} hours, {ptf.index.min()} .. {ptf.index.max()}")

        reports = {}
        for use_lp in (True, False):
            if use_lp and "load_forecast_mwh" not in frame:
                continue
            print(f"\nBacktesting (load plan feature: {use_lp}) ...")
            reports[use_lp] = forecasting.backtest(frame, args.test_weeks, use_load_plan=use_lp)
            print(json.dumps(reports[use_lp], indent=2))

        # Ship the load-plan variant only if it actually beats the one
        # without it on held-out weeks.
        use_lp = bool(
            reports.get(True)
            and reports[True]["models"]["xgboost_p50"]["mae"] < reports[False]["models"]["xgboost_p50"]["mae"]
        )
        model = forecasting.train(frame, use_load_plan=use_lp)
        forecasting.save(model, service.MODEL_DIR, reports[use_lp])
        print(f"\nSaved model (load plan: {use_lp}) to {service.MODEL_DIR}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
