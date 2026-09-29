"""
Synthetic demo site: physics, determinism, and that it flows through
the production pipeline exactly like real telemetry would.
"""

import uuid
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.database.session import SessionLocal
from app.jobs.device_jobs import get_active_devices
from app.models.device import Device
from app.models.energy_hourly import EnergyHourly
from app.models.user import User
from app.modules.auth.service import register_user
from app.modules.demo import seed
from app.modules.demo.synthetic import SYNTHETIC_MARKER, SiteSpec, simulate

T0 = pd.Timestamp("2026-09-15", tz="UTC")


def _series(frames, key, col="power_kw"):
    return frames[key].set_index("timestamp")[col]


def test_site_energy_balances_every_sample():
    f = simulate(SiteSpec(), T0, T0 + pd.Timedelta(days=3), "5min")
    pv = _series(f, "inverter_a") + _series(f, "inverter_b")
    raw = f["grid_meter"].set_index("timestamp")["raw_data"]
    imp = raw.map(lambda r: r["import_power_kw"])
    exp = raw.map(lambda r: r["export_power_kw"])
    batt = _series(f, "battery")  # + charging, - discharging
    load = _series(f, "factory_meter")
    assert (pv + imp - load - exp - batt).abs().max() < 0.01


def test_physical_bounds_hold():
    spec = SiteSpec()
    f = simulate(spec, T0, T0 + pd.Timedelta(days=7), "5min")
    for inv in spec.inverters:
        p = _series(f, inv.key)
        assert p.min() >= 0 and p.max() <= inv.rated_kw
    soc = _series(f, "battery", "soc_percent")
    assert soc.min() >= spec.battery.min_soc - 0.01 and soc.max() <= spec.battery.max_soc + 0.01
    assert _series(f, "battery").abs().max() <= spec.battery.power_kw + 1e-6
    # No generation at night (local midnight-4am).
    night = _series(f, "inverter_a")[lambda s: s.index.tz_convert(spec.timezone).hour < 4]
    assert night.max() == 0


def test_samples_are_identical_across_window_boundaries():
    """Extension runs must continue the same series a backfill produced."""
    spec = SiteSpec(soiling_start=T0)
    whole = simulate(spec, T0, T0 + pd.Timedelta(days=2), "5min")
    later = simulate(spec, T0 + pd.Timedelta(days=1), T0 + pd.Timedelta(days=2), "5min")
    a = _series(whole, "inverter_b").loc[T0 + pd.Timedelta(days=1):]
    b = _series(later, "inverter_b")
    assert np.allclose(a.to_numpy(), b.to_numpy())


def test_inverter_b_soils_while_a_stays_clean():
    spec = SiteSpec(soiling_start=T0)
    f = simulate(spec, T0, T0 + pd.Timedelta(days=14), "15min")
    irr = f["inverter_a"].set_index("timestamp")["raw_data"].map(lambda r: r["irradiance_w_m2"])
    lit = irr > 300

    def pr(key, rated=500.0):
        p = _series(f, key)[lit]
        return (p.resample("D").sum() / (rated * irr[lit] / 1000).resample("D").sum()).dropna()

    a, b = pr("inverter_a"), pr("inverter_b")
    assert b.iloc[-1] < b.iloc[0] - 0.1
    assert abs(a.iloc[-1] - a.iloc[0]) < 0.05


def test_poll_loop_skips_push_devices():
    db = SessionLocal()
    try:
        polled = get_active_devices(db)
        assert all(d.connection_type != "API" for d in polled)
    finally:
        db.close()


def test_seeded_demo_flows_through_production_aggregation():
    db = SessionLocal()
    factory = None
    try:
        user = register_user(
            db, email=f"demo-test-{uuid.uuid4().hex[:8]}@pytest.solarflow.com",
            password="TestPass123!", full_name="Demo Test", organization_name="Demo Test Org",
        )
        user = db.get(User, user.id)
        spec = SiteSpec()
        factory = seed.create_demo_site(db, user, spec)
        end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=2)
        n = seed.write_readings(db, factory, SiteSpec(soiling_start=pd.Timestamp(start)), start, end)
        assert n > 0

        devices = db.scalars(select(Device).where(Device.factory_id == factory.id)).all()
        assert {d.device_type for d in devices} == {"INVERTER", "BATTERY", "FACTORY_METER", "GRID_METER"}
        assert all(d.manufacturer == SYNTHETIC_MARKER and d.connection_type == "API" for d in devices)

        hours = seed.aggregate(db, factory, start, end)
        assert hours == 48
        rows = db.scalars(select(EnergyHourly).where(EnergyHourly.factory_id == factory.id)).all()
        assert len(rows) == 48
        assert sum(r.solar_kwh for r in rows) > 0 and sum(r.consumption_kwh for r in rows) > 0
        # Hourly energy balance survives aggregation (±1% for integration rounding).
        supply = sum(r.solar_kwh + r.grid_import_kwh + r.battery_discharge_kwh for r in rows)
        demand = sum(r.consumption_kwh + r.grid_export_kwh + r.battery_charge_kwh for r in rows)
        assert abs(supply - demand) / demand < 0.01

        # Top-up is idempotent: nothing new to write right after a backfill.
        assert seed.extend_to_now(db, factory, seed.spec_for(db, factory)) >= 0
    finally:
        if factory is not None:
            seed.purge(db, factory)
        db.close()
