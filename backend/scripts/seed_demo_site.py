"""
Seed (or refresh) the synthetic demo factory and run the whole pipeline
on it end to end.

    python scripts/seed_demo_site.py            # create if missing, else top up to now
    python scripts/seed_demo_site.py --reset    # delete the demo factory and rebuild
    python scripts/seed_demo_site.py --days 21

What it does:
  1. demo company + login (COMPANY_ADMIN, verified), factory in Konya,
     2 x 500 kW inverters (B slowly soiling), 1.2 MWh battery,
     factory meter, grid meter — all push-type "SYNTHETIC" devices
  2. --days of device telemetry (5-min, last 36 h at 1-min)
  3. production hourly/daily aggregation over that history
  4. tomorrow's solar forecast (real Open-Meteo, synthetic fallback)
  5. failure-risk assessment of every device
  6. PTF forecast for the next delivery day (trained model or baseline)
  7. a GÖP sell offer for that day

All telemetry is synthetic (raw_data.source == "SYNTHETIC"); PTF data
is whatever real EPİAŞ history is in the DB.
"""

import argparse
import asyncio
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.modules.auth.service import register_user  # noqa: E402
from app.modules.demo import seed  # noqa: E402
from app.modules.failure_prediction.service import assess_factory  # noqa: E402
from app.modules.market import service as market  # noqa: E402

DEMO_EMAIL = "demo@solarflow.local"


def _demo_user(db, email: str, password: str | None) -> tuple[User, str | None]:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user, None
    password = password or secrets.token_urlsafe(12)
    user = register_user(db, email=email, password=password, full_name="Demo Operator",
                         organization_name="SolarFlow Demo")
    user.is_verified = True
    db.commit()
    return user, password


async def run(args) -> None:
    db = SessionLocal()
    try:
        factory = seed.get_demo_factory(db)
        if factory and args.reset:
            print(f"Removing demo factory #{factory.id} ...")
            seed.purge(db, factory)
            factory = None

        new_password = None
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if factory is None:
            user, new_password = _demo_user(db, args.email, args.password)
            factory = seed.create_demo_site(db, user, seed.SiteSpec())
            start = now - timedelta(days=args.days)
            spec = seed.SiteSpec(soiling_start=seed.pd.Timestamp(start))
            print(f"Created demo factory #{factory.id}; writing {args.days} days of telemetry ...")
            n = seed.write_readings(db, factory, spec, start, now)
            agg_from = start
        else:
            spec = seed.spec_for(db, factory)
            last = seed.latest_reading_at(db, factory)
            print(f"Demo factory #{factory.id} exists; topping up telemetry from {last} ...")
            n = seed.extend_to_now(db, factory, spec)
            agg_from = last or now - timedelta(days=args.days)
        print(f"  {n:,} device readings written")

        hours = seed.aggregate(db, factory, agg_from, now)
        print(f"  {hours} hours aggregated through the production pipeline")

        source = await seed.ensure_solar_forecast(db, factory, spec)
        print(f"  solar forecast: {source}")

        assessments = assess_factory(db, factory, weather=None, notify=True)
        print("\nFailure risk:")
        for a in sorted(assessments, key=lambda a: -a.risk_score):
            print(f"  device {a.device_id} {a.device_type:13} {a.risk_level:8} {a.risk_score:5.1f}  "
                  f"top={a.top_reason}  ml={a.ml_status}"
                  + (f"  p(fault 3h)={a.failure_probability:.2f}" if a.failure_probability is not None else ""))

        delivery = market.next_delivery_date()
        try:
            forecast = market.issue_forecast(db, delivery)
            print(f"\nPTF forecast {delivery} ({forecast[0].model_version}): "
                  f"mean P50 {sum(f.p50_try_mwh for f in forecast) / 24:,.0f} TL/MWh")
            rows, notes = market.generate_offer(db, factory, delivery, mode="GOP_BID", min_price=0.0)
            sold = sum(r.quantity_mwh for r in rows if r.action in ("SELL", "DISCHARGE_SELL"))
            revenue = sum(r.expected_revenue_try or 0 for r in rows)
            print(f"Sell offer {delivery}: {len(rows)} bid rows, {sold:.1f} MWh, expected ₺{revenue:,.0f}")
            for note in notes:
                print(f"  note: {note}")
        except market.OfferError as error:
            print(f"\nNo PTF forecast/offer: {error}")

        print(f"\nDemo factory id: {factory.id}")
        print(f"Login: {args.email}" + (f"  password: {new_password}" if new_password else "  (existing account)"))
        print(f"Frontend: set NEXT_PUBLIC_FACTORY_ID={factory.id} in .env.local")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--email", default=DEMO_EMAIL)
    parser.add_argument("--password", default=None)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
