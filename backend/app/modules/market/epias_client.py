"""
EPİAŞ Transparency Platform client (seffaflik.epias.com.tr).

Auth: POST username/password to the CAS ticket endpoint -> a TGT
("ticket granting ticket") string, sent as the `TGT` header on every
data call. TGTs live ~2 hours; one is cached per process and refreshed
early, and a 401 on a data call forces one re-login and retry.

Every data call is `POST {base}{path}` with a JSON body holding
startDate/endDate as ISO-8601 with the +03:00 offset (Turkey has had no
DST since 2016, so every EPİAŞ hour is exactly UTC+3). Long ranges are
split into CHUNK_DAYS windows — the platform rejects or truncates wide
ranges on several endpoints.

Returned rows are normalised to {"timestamp": aware datetime, ...} so
nothing downstream parses EPİAŞ's field naming.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone

import httpx

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.core.config import settings
from app.core.external_api_metrics import record_external_call

TR_TZ = timezone(timedelta(hours=3))
CHUNK_DAYS = 31
TGT_TTL_SECONDS = 100 * 60  # EPİAŞ issues ~2 h tickets; refresh early
TRANSPORT_RETRIES = 3

PATHS = {
    "ptf": "/v1/markets/dam/data/mcp",
    "smf": "/v1/markets/bpm/data/system-marginal-price",
    "load_plan": "/v1/consumption/data/load-estimation-plan",
    "dpp": "/v1/generation/data/dpp",
}

_epias_circuit_breaker = CircuitBreaker(
    name="epias",
    failure_threshold=5,
    recovery_timeout_seconds=120.0,
)


class EpiasNotConfiguredError(RuntimeError):
    pass


class EpiasAuthError(RuntimeError):
    pass


_tgt: str | None = None
_tgt_obtained_at = 0.0
_tgt_lock = asyncio.Lock()


def is_configured() -> bool:
    return bool(settings.EPIAS_USERNAME and settings.EPIAS_PASSWORD)


async def _login(client: httpx.AsyncClient) -> str:
    if not is_configured():
        raise EpiasNotConfiguredError(
            "EPIAS_USERNAME / EPIAS_PASSWORD are not set in backend/.env"
        )
    response = await client.post(
        settings.EPIAS_AUTH_URL,
        data={"username": settings.EPIAS_USERNAME, "password": settings.EPIAS_PASSWORD},
        headers={"Accept": "text/plain"},
    )
    ticket = response.text.strip()
    if response.status_code not in (200, 201) or not ticket.startswith("TGT-"):
        # Never echo the response body: on some failures CAS reflects
        # the submitted form back.
        raise EpiasAuthError(f"EPİAŞ login failed (HTTP {response.status_code})")
    return ticket


async def _get_tgt(client: httpx.AsyncClient, force: bool = False) -> str:
    global _tgt, _tgt_obtained_at
    async with _tgt_lock:
        if force or _tgt is None or time.monotonic() - _tgt_obtained_at > TGT_TTL_SECONDS:
            _tgt = await _login(client)
            _tgt_obtained_at = time.monotonic()
        return _tgt


def _iso(dt: datetime) -> str:
    return dt.astimezone(TR_TZ).isoformat(timespec="seconds")


async def _post(client: httpx.AsyncClient, path: str, body: dict) -> dict:
    start = time.monotonic()

    async def _send(tgt: str) -> httpx.Response:
        # The platform occasionally drops a connection mid-backfill
        # ("Server disconnected without sending a response"); retry
        # transport-level failures with backoff, never HTTP errors.
        for attempt in range(TRANSPORT_RETRIES):
            try:
                return await client.post(settings.EPIAS_BASE_URL + path, json=body, headers={"TGT": tgt})
            except (httpx.TransportError, httpx.TimeoutException):
                if attempt == TRANSPORT_RETRIES - 1:
                    raise
                await asyncio.sleep(2 * (attempt + 1))
        raise AssertionError("unreachable")

    async def _do() -> dict:
        response = await _send(await _get_tgt(client))
        if response.status_code == 401:
            response = await _send(await _get_tgt(client, force=True))
        response.raise_for_status()
        return response.json()

    try:
        data = await _epias_circuit_breaker.call(_do)
    except CircuitBreakerOpenError:
        record_external_call("epias", success=False, latency_ms=0.0)
        raise
    except httpx.TimeoutException:
        record_external_call("epias", success=False, latency_ms=(time.monotonic() - start) * 1000, timed_out=True)
        raise
    except Exception:
        record_external_call("epias", success=False, latency_ms=(time.monotonic() - start) * 1000)
        raise
    record_external_call("epias", success=True, latency_ms=(time.monotonic() - start) * 1000)
    return data


def _chunks(start: datetime, end: datetime):
    cursor = start
    while cursor < end:
        chunk_end = min(cursor + timedelta(days=CHUNK_DAYS), end)
        yield cursor, chunk_end
        cursor = chunk_end


def _row_timestamp(item: dict) -> datetime:
    """`date` carries the full hour timestamp on every endpoint seen so
    far ("2026-09-27T13:00:00+03:00"). `hour`/`time` vary — "13:00" on
    some, a full ISO timestamp on others (SMF) — so they're only
    consulted as a fallback when `date` is a bare midnight and the
    field is a plain "HH:MM"."""
    ts = datetime.fromisoformat(item["date"])
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=TR_TZ)
    hour_str = item.get("hour") or item.get("time")
    if ts.hour == 0 and isinstance(hour_str, str) and len(hour_str) == 5 and hour_str[2] == ":":
        ts = ts.replace(hour=int(hour_str[:2]))
    return ts.astimezone(timezone.utc)


def _in_window(rows: list[dict], start: datetime, end: datetime) -> list[dict]:
    """Some endpoints round endDate up to a whole day and return extra
    hours; keep exactly [start, end)."""
    return [r for r in rows if start <= r["timestamp"] < end]


def _first(item: dict, *keys: str) -> float | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


async def _fetch(name: str, start: datetime, end: datetime, extra: dict | None = None) -> list[dict]:
    """Inclusive start, exclusive end (hour granularity)."""
    rows: list[dict] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for chunk_start, chunk_end in _chunks(start, end):
            body = {
                "startDate": _iso(chunk_start),
                # EPİAŞ endDate is inclusive of the whole day it names;
                # step back one hour so chunks don't overlap.
                "endDate": _iso(chunk_end - timedelta(hours=1)),
                **(extra or {}),
            }
            data = await _post(client, PATHS[name], body)
            rows.extend(data.get("items") or data.get("body", {}).get("items") or [])
    return rows


async def fetch_ptf(start: datetime, end: datetime) -> list[dict]:
    rows = [
        {
            "timestamp": _row_timestamp(i),
            "ptf_try_mwh": _first(i, "price", "marketTradePrice"),
            "ptf_usd_mwh": _first(i, "priceUsd"),
            "ptf_eur_mwh": _first(i, "priceEur"),
        }
        for i in await _fetch("ptf", start, end)
    ]
    return _in_window(rows, start, end)


async def fetch_smf(start: datetime, end: datetime) -> list[dict]:
    """SMF is settled after delivery, and the endpoint rejects any
    endDate not in the past ((VAL)SEF1116) — so unlike PTF (published
    for tomorrow) the window is clamped to the current hour."""
    end = min(end, datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0))
    if end <= start:
        return []
    rows = [
        {"timestamp": _row_timestamp(i), "smf_try_mwh": _first(i, "systemMarginalPrice", "smp", "price")}
        for i in await _fetch("smf", start, end)
    ]
    return _in_window(rows, start, end)


async def fetch_load_plan(start: datetime, end: datetime) -> list[dict]:
    """Yük Tahmin Planı (LEP) — TEİAŞ's demand forecast, published the
    day before delivery, so it's a legitimate feature for D+1."""
    rows = [
        {"timestamp": _row_timestamp(i), "load_forecast_mwh": _first(i, "lep", "loadEstimationPlan")}
        for i in await _fetch("load_plan", start, end)
    ]
    return _in_window(rows, start, end)


async def fetch_dpp(start: datetime, end: datetime) -> list[dict]:
    """KGÜP (Kesinleşmiş Günlük Üretim Planı) — finalised generation
    plans by source. Finalised *after* the day-ahead auction for that
    day, so when bidding for D+1 at 12:30 on D only D's plan (and
    earlier) is known: use it lagged >= 24 h, never same-day."""
    rows = [
        {
            "timestamp": _row_timestamp(i),
            "dpp_total_mwh": _first(i, "toplam", "total"),
            "dpp_wind_mwh": _first(i, "ruzgar", "wind"),
            "dpp_solar_mwh": _first(i, "gunes", "sun", "solar"),
            "dpp_hydro_mwh": _first(i, "barajli", "dammedHydro"),
            "dpp_river_mwh": _first(i, "akarsu", "river"),
            "dpp_natural_gas_mwh": _first(i, "dogalgaz", "naturalGas"),
            "dpp_lignite_mwh": _first(i, "linyit", "lignite"),
            "dpp_imported_coal_mwh": _first(i, "ithalKomur", "importCoal"),
        }
        for i in await _fetch("dpp", start, end, {"region": "TR1"})
    ]
    return _in_window(rows, start, end)
