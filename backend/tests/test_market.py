"""
Day-ahead market: EPİAŞ client, PTF forecasting, offer builder, API.

Market tables are market-wide (one national PTF) and tests share the
dev database, so every price row written here is dated 2005 — years
before PTF existed (Dec 2011) — and deleted afterwards. All prices in
this file are SYNTHETIC test fixtures, not market data.
"""

import asyncio
import math
import uuid
from datetime import date, datetime, timedelta, timezone

import httpx
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.main import app
from app.models.energy_hourly import EnergyHourly
from app.models.solar_forecast import SolarForecast
from app.modules.market import epias_client, forecasting, service
from app.modules.market.models import MarketFundamental, MarketPrice, PtfForecast
from app.modules.market.offer import LOT_MWH, BatterySpec, build_offer, plan_battery

client = TestClient(app)
TR = forecasting.TR_TZ


def synthetic_market(days: int = 300, start: str = "2004-06-01", seed: int = 1) -> pd.DataFrame:
    """Load-driven synthetic PTF: price ~ level * (load/base)^2 with a
    midday solar dip, weekend drop, slow inflation drift and noise."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=days * 24, freq="h", tz=TR).tz_convert("UTC")
    loc = idx.tz_convert(TR)
    h, dow = loc.hour.to_numpy(), loc.dayofweek.to_numpy()
    wk = np.where(dow >= 5, 0.82, 1.0)
    day_shock = np.repeat(rng.normal(0, 1, days), 24)
    load = (30000 + 7000 * np.sin((h - 6) / 24 * 2 * np.pi)) * wk * (1 + 0.06 * day_shock)
    load += rng.normal(0, 400, len(idx))
    level = 1500 * 1.0015 ** (np.arange(len(idx)) / 24)
    ptf = level * (load / 30000) ** 2 * (1 - 0.3 * np.exp(-(((h - 13) / 2.5) ** 2)))
    ptf *= 1 + rng.normal(0, 0.04, len(idx))
    return pd.DataFrame({"ptf": ptf, "load_forecast_mwh": load}, index=idx)


# --- EPİAŞ client ---


def _mock_transport(calls: list):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if "cas/v1/tickets" in str(request.url):
            return httpx.Response(201, text="TGT-123-test")
        if request.headers.get("TGT") != "TGT-123-test":
            return httpx.Response(401, json={"errors": [{"errorCode": "AUTH002"}]})
        return httpx.Response(200, json={"items": [
            {"date": "2026-09-27T00:00:00+03:00", "hour": "00:00", "price": 2500.5, "priceUsd": 60.1, "priceEur": 55.2},
            {"date": "2026-09-27T01:00:00+03:00", "hour": "01:00", "price": 2400.0, "priceUsd": 57.7, "priceEur": 53.0},
        ]})
    return httpx.MockTransport(handler)


def test_epias_client_logs_in_and_parses_ptf(monkeypatch):
    calls: list = []
    real = httpx.AsyncClient
    monkeypatch.setattr(epias_client.httpx, "AsyncClient", lambda **kw: real(transport=_mock_transport(calls), **kw))
    monkeypatch.setattr(epias_client.settings, "EPIAS_USERNAME", "user@test")
    monkeypatch.setattr(epias_client.settings, "EPIAS_PASSWORD", "secret")
    monkeypatch.setattr(epias_client, "_tgt", None)

    start = datetime(2026, 9, 26, 21, tzinfo=timezone.utc)
    rows = asyncio.run(epias_client.fetch_ptf(start, start + timedelta(days=1)))

    assert rows[0]["timestamp"] == datetime(2026, 9, 26, 21, tzinfo=timezone.utc)  # 00:00 TR
    assert rows[1]["ptf_try_mwh"] == 2400.0 and rows[0]["ptf_usd_mwh"] == 60.1
    data_calls = [c for c in calls if "mcp" in str(c.url)]
    assert data_calls[0].headers["TGT"] == "TGT-123-test"
    body = data_calls[0].read().decode()
    assert "+03:00" in body


def test_epias_client_refuses_without_credentials(monkeypatch):
    monkeypatch.setattr(epias_client.settings, "EPIAS_USERNAME", "")
    monkeypatch.setattr(epias_client, "_tgt", None)
    with pytest.raises(epias_client.EpiasNotConfiguredError):
        asyncio.run(epias_client.fetch_ptf(datetime(2026, 9, 1, tzinfo=timezone.utc), datetime(2026, 9, 2, tzinfo=timezone.utc)))


# --- Forecasting ---


def test_features_never_see_the_delivery_day():
    """Changing every price from the delivery day on must not change
    that day's forecast — the model may only use what a bidder knew
    at 12:30 the day before."""
    frame = synthetic_market(200)
    model = forecasting.train(frame, use_load_plan=True)
    day = (frame.index[-1].tz_convert(TR) - pd.Timedelta(days=20)).date()
    first_hour = forecasting.delivery_hours(day)[0]

    a = forecasting.predict(model, frame, day)
    tampered = frame.copy()
    tampered.loc[tampered.index >= first_hour, "ptf"] *= 7
    b = forecasting.predict(model, tampered, day)
    assert np.allclose(a.to_numpy(), b.to_numpy())


def test_quantiles_are_ordered_and_capped():
    frame = synthetic_market(200)
    model = forecasting.train(frame)
    model.cap = 2000.0
    day = (frame.index[-1].tz_convert(TR) + pd.Timedelta(days=1)).date()
    q = forecasting.predict(model, frame, day)
    assert len(q) == 24
    assert (q["p10"] <= q["p50"]).all() and (q["p50"] <= q["p90"]).all()
    assert q.to_numpy().max() <= 2000.0 and q.to_numpy().min() >= 0


def test_backtest_beats_naive_when_structure_exists():
    report = forecasting.backtest(synthetic_market(220), test_weeks=2)
    models = report["models"]
    assert models["xgboost_p50"]["mae"] < models["baseline_avg_d1_d7"]["mae"]
    assert report["skill_vs_best_naive_pct"] > 0
    assert 40 <= report["interval"]["p10_p90_coverage_pct"] <= 100


def test_baseline_forecast_uses_d1_and_d7():
    frame = synthetic_market(30)
    day = (frame.index[-1].tz_convert(TR) + pd.Timedelta(days=1)).date()
    base = forecasting.baseline_forecast(frame, day)
    ts = base.index[5]
    expected = (frame["ptf"][ts - pd.Timedelta(hours=24)] + frame["ptf"][ts - pd.Timedelta(hours=168)]) / 2
    assert base.at[ts, "p50"] == pytest.approx(expected)


# --- Offer builder ---


def _day(prices: np.ndarray) -> tuple[pd.DatetimeIndex, pd.DataFrame]:
    ts = forecasting.delivery_hours(date(2005, 6, 15))
    return ts, pd.DataFrame({"p10": prices * 0.8, "p50": prices, "p90": prices * 1.2}, index=ts)


def test_battery_charges_cheap_and_discharges_later_within_limits():
    h = np.arange(24)
    surplus = np.where((h >= 10) & (h <= 14), 400.0, 0.0)
    p50 = np.where((h >= 10) & (h <= 14), 500.0, 3000.0)
    battery = BatterySpec(usable_kwh=600, charge_kw=250, discharge_kw=300, efficiency=0.9)
    charge, discharge, moves = plan_battery(surplus, p50, battery)

    assert charge.sum() == pytest.approx(600)  # capacity-bound
    assert charge.max() <= 250 + 1e-9 and discharge.max() <= 300 + 1e-9
    assert discharge.sum() == pytest.approx(600 * 0.9)
    assert all(c < d for c, d, _ in moves)
    assert (charge <= surplus + 1e-9).all()


def test_battery_idles_when_spread_does_not_cover_losses():
    surplus = np.full(24, 300.0)
    p50 = np.full(24, 1000.0)
    p50[20] = 1080.0  # 1080 * 0.9 < 1000
    charge, discharge, _ = plan_battery(surplus, p50, BatterySpec(500, 250, 250, 0.9))
    assert charge.sum() == 0 and discharge.sum() == 0


def test_gop_offer_rounds_to_lots_and_prices_tiers():
    h = np.arange(24)
    pv = np.where((h >= 8) & (h <= 16), 650.0, 0.0)
    load = np.full(24, 100.0)
    prices = np.where(h >= 18, 3000.0, 800.0).astype(float)
    ts, ptf = _day(prices)
    plan = build_offer(ts, pv, load, ptf, mode="GOP_BID", min_price=50.0,
                       battery=BatterySpec(1000, 500, 500, 0.9))

    tier1 = [x for x in plan.hours if x.tier == 1]
    tier2 = [x for x in plan.hours if x.tier == 2]
    assert tier1 and tier2
    for x in plan.hours:
        assert math.isclose(x.quantity_mwh / LOT_MWH, round(x.quantity_mwh / LOT_MWH), abs_tol=1e-9)
    assert all(x.price_try_mwh == 50.0 for x in tier1)
    # Discharge bid covers the charge-hour price after losses: 800/0.9
    assert all(x.price_try_mwh == pytest.approx(888.89, abs=0.01) for x in tier2)
    assert plan.unbid_remainder_mwh >= 0


def test_net_metering_plan_has_no_bid_prices():
    h = np.arange(24)
    pv = np.where((h >= 8) & (h <= 16), 650.0, 0.0)
    ts, ptf = _day(np.full(24, 1000.0))
    plan = build_offer(ts, pv, np.full(24, 100.0), ptf, mode="NET_METERING")
    assert plan.hours and all(x.price_try_mwh is None for x in plan.hours)
    assert plan.expected_revenue == pytest.approx(sum(max(0, p - 100) for p in pv) / 1000 * 1000)


# --- API (real DB, 2005-dated synthetic rows) ---


@pytest.fixture
def seeded_market():
    frame = synthetic_market(60, start="2005-04-01")
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        db.add_all([MarketPrice(timestamp=ts.to_pydatetime(), ptf_try_mwh=float(r.ptf), source="TEST", updated_at=now)
                    for ts, r in frame.iterrows()])
        db.commit()
        yield frame
    finally:
        lo, hi = datetime(2005, 1, 1, tzinfo=timezone.utc), datetime(2006, 1, 1, tzinfo=timezone.utc)
        db.execute(delete(PtfForecast).where(PtfForecast.timestamp >= lo, PtfForecast.timestamp < hi))
        db.execute(delete(MarketPrice).where(MarketPrice.timestamp >= lo, MarketPrice.timestamp < hi))
        db.execute(delete(MarketFundamental).where(MarketFundamental.timestamp >= lo, MarketFundamental.timestamp < hi))
        db.commit()
        db.close()


def _admin() -> dict:
    email = f"market-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "TestPass123!", "full_name": "Market Admin", "organization_name": "Market Org",
    })
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _delivery_after(frame: pd.DataFrame) -> date:
    return (frame.index[-1].tz_convert(TR) + pd.Timedelta(days=1)).date()


def test_forecast_endpoint_falls_back_to_baseline(seeded_market, monkeypatch):
    monkeypatch.setattr(service, "get_model", lambda: None)
    headers = _admin()
    day = _delivery_after(seeded_market)
    res = client.get(f"/api/v1/market/ptf/forecast?delivery_date={day}", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["model_version"] == forecasting.BASELINE_VERSION
    assert len(body["points"]) == 24


def test_sell_offer_end_to_end(seeded_market, monkeypatch):
    monkeypatch.setattr(service, "get_model", lambda: None)
    headers = _admin()
    factory = client.post("/api/v1/factories", json={"name": "Market Factory", "solar_capacity_kw": 2000}, headers=headers).json()
    fid = factory["id"]
    day = _delivery_after(seeded_market)
    hours = forecasting.delivery_hours(day)

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for ts in hours:
            h = ts.tz_convert(TR).hour
            kwh = max(0.0, 1800 * math.sin(math.pi * (h - 6) / 13))
            db.add(SolarForecast(factory_id=fid, timestamp=ts.to_pydatetime(), expected_power_kw=kwh,
                                 expected_energy_kwh=kwh, confidence=0.8, created_at=now))
        for k in range(1, 15 * 24):
            ts = hours[0] - pd.Timedelta(hours=k)
            db.add(EnergyHourly(factory_id=fid, hour=ts.to_pydatetime(), consumption_kwh=400.0))
        db.commit()
    finally:
        db.close()

    res = client.post(f"/api/v1/factories/{fid}/sell-offers",
                      json={"delivery_date": str(day), "mode": "GOP_BID", "min_price_try_mwh": 10}, headers=headers)
    assert res.status_code == 200, res.text
    offer = res.json()
    assert offer["status"] == "DRAFT" and offer["rows"]
    assert offer["total_quantity_mwh"] > 0
    assert offer["revenue_p10_try"] <= offer["expected_revenue_try"] <= offer["revenue_p90_try"]
    assert all(r["price_try_mwh"] == 10 for r in offer["rows"] if r["tier"] == 1)

    sub = client.post(f"/api/v1/factories/{fid}/sell-offers/mark-submitted?delivery_date={day}", headers=headers)
    assert sub.json()["status"] == "SUBMITTED"
    again = client.post(f"/api/v1/factories/{fid}/sell-offers", json={"delivery_date": str(day)}, headers=headers)
    assert again.status_code == 409

    outsider = _admin()
    assert client.get(f"/api/v1/factories/{fid}/sell-offers?delivery_date={day}", headers=outsider).status_code == 404


def test_offer_without_consumption_history_is_refused(seeded_market, monkeypatch):
    monkeypatch.setattr(service, "get_model", lambda: None)
    headers = _admin()
    fid = client.post("/api/v1/factories", json={"name": "No History", "solar_capacity_kw": 500}, headers=headers).json()["id"]
    day = _delivery_after(seeded_market)
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        db.add_all([SolarForecast(factory_id=fid, timestamp=ts.to_pydatetime(), expected_power_kw=100,
                                  expected_energy_kwh=100, confidence=0.8, created_at=now)
                    for ts in forecasting.delivery_hours(day)])
        db.commit()
    finally:
        db.close()
    res = client.post(f"/api/v1/factories/{fid}/sell-offers", json={"delivery_date": str(day)}, headers=headers)
    assert res.status_code == 409 and "consumption history" in res.json()["detail"]


def test_sync_endpoint_upserts_and_merges(seeded_market, monkeypatch):
    ts = datetime(2005, 3, 1, 9, tzinfo=timezone.utc)

    async def fake_ptf(start, end):
        return [{"timestamp": ts, "ptf_try_mwh": 1234.5, "ptf_usd_mwh": None, "ptf_eur_mwh": None}]

    async def fake_smf(start, end):
        return [{"timestamp": ts, "smf_try_mwh": 1300.0}]

    async def fake_empty(start, end):
        return []

    monkeypatch.setattr(service.epias_client, "fetch_ptf", fake_ptf)
    monkeypatch.setattr(service.epias_client, "fetch_smf", fake_smf)
    monkeypatch.setattr(service.epias_client, "fetch_load_plan", fake_empty)
    monkeypatch.setattr(service.epias_client, "fetch_dpp", fake_empty)
    monkeypatch.setattr(epias_client, "is_configured", lambda: True)

    res = client.post("/api/v1/market/sync", json={"days": 3}, headers=_admin())
    assert res.status_code == 200, res.text
    db = SessionLocal()
    try:
        row = db.query(MarketPrice).filter(MarketPrice.timestamp == ts).one()
        assert row.ptf_try_mwh == 1234.5 and row.smf_try_mwh == 1300.0
    finally:
        db.close()
