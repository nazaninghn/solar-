"""
Day-ahead market jobs, scheduled on Turkey time around the GÖP calendar:

  10:00  sync recent data, forecast tomorrow's PTF, draft sell offers
         for every factory with PV — 2.5 h before the 12:30 gate closure
  14:30  pull the day-ahead results published ~14:00 (tomorrow's actual
         PTF), which is also what tomorrow's forecast gets scored against
  Sun 03:00  retrain the PTF model on all history + fresh backtest

Every job records itself "skipped" (not failed) while EPİAŞ credentials
aren't configured — same convention as update_electricity_prices.
"""

import logging

import pandas as pd

from app.core.config import settings
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.market import epias_client, forecasting, service

logger = logging.getLogger(__name__)

TR = forecasting.TR_TZ
RETRAIN_BACKTEST_WEEKS = 8


def _window(days_back: int) -> tuple:
    today = pd.Timestamp.now(tz=TR).normalize()
    start = (today - pd.Timedelta(days=days_back)).tz_convert("UTC").to_pydatetime()
    end = (today + pd.Timedelta(days=2)).tz_convert("UTC").to_pydatetime()
    return start, end


def _skip_unconfigured(db, job_run) -> bool:
    if epias_client.is_configured():
        return False
    finish_job_run(db, job_run, status="skipped", error_message="EPİAŞ credentials not configured")
    return True


async def sync_market_prices() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "sync_market_prices")
    try:
        if _skip_unconfigured(db, job_run):
            return
        result = await service.sync_market(db, *_window(3))
        finish_job_run(
            db, job_run,
            status="failed" if result["errors"] else "success",
            error_message=str(result["errors"]) if result["errors"] else None,
        )
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error)[:500])
        raise
    finally:
        db.close()


async def forecast_and_draft_offers() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "forecast_ptf_and_draft_offers")
    try:
        if _skip_unconfigured(db, job_run):
            return
        await service.sync_market(db, *_window(2))
        delivery_date = service.next_delivery_date()
        service.issue_forecast(db, delivery_date)

        failed = {}
        for factory in get_all_factories(db):
            if not factory.solar_capacity_kw:
                continue
            try:
                service.generate_offer(db, factory, delivery_date)
            except service.OfferError as error:
                # Expected for factories without a solar forecast or
                # consumption history yet — not a job failure.
                logger.info("No offer for factory %s: %s", factory.id, error)
            except Exception as error:
                db.rollback()
                failed[factory.id] = str(error)[:120]

        finish_job_run(
            db, job_run,
            status="failed" if failed else "success",
            error_message=f"Offer generation failed: {failed}" if failed else None,
        )
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error)[:500])
        raise
    finally:
        db.close()


def retrain_ptf_model() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "retrain_ptf_model")
    try:
        frame = service.load_frame(db)
        days = frame["ptf"].dropna().index.normalize().nunique() if not frame.empty else 0
        if days < forecasting.MIN_TRAIN_DAYS + 7 * RETRAIN_BACKTEST_WEEKS:
            finish_job_run(db, job_run, status="skipped", error_message=f"Only {days} days of PTF history")
            return
        report = forecasting.backtest(frame, test_weeks=RETRAIN_BACKTEST_WEEKS)
        model = forecasting.train(frame)
        forecasting.save(model, service.MODEL_DIR, report)
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error)[:500])
        raise
    finally:
        db.close()


def register_market_jobs() -> None:
    scheduler.add_job(
        forecast_and_draft_offers, "cron", hour=10, minute=0, timezone=TR,
        id="forecast_ptf_and_draft_offers", replace_existing=True,
    )
    scheduler.add_job(
        sync_market_prices, "cron", hour=14, minute=30, timezone=TR,
        id="sync_market_prices", replace_existing=True,
    )
    scheduler.add_job(
        retrain_ptf_model, "cron", day_of_week="sun", hour=3, minute=0, timezone=TR,
        id="retrain_ptf_model", replace_existing=True,
    )
