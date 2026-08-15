"""
Huawei FusionSolar API Client.

Connects to Huawei's iMaster NetEco / FusionSolar cloud platform
to pull real-time and historical data from Huawei inverters.

API docs: https://support.huawei.com/enterprise/en/doc/EDOC1100261860

Authentication: username + password → XSRF token (valid 30 min).
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Huawei FusionSolar API base URLs
FUSIONSOLAR_EU_URL = "https://eu5.fusionsolar.huawei.com/thirdData"
FUSIONSOLAR_INTL_URL = "https://intl.fusionsolar.huawei.com/thirdData"


class HuaweiFusionSolarClient:
    """Client for Huawei FusionSolar Third-Party API."""

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = FUSIONSOLAR_INTL_URL,
    ):
        self.username = username
        self.password = password
        self.base_url = base_url
        self._token: str | None = None
        self._token_expires: datetime | None = None

    async def _authenticate(self) -> None:
        """Login and get XSRF-TOKEN."""
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                f"{self.base_url}/login",
                json={
                    "userName": self.username,
                    "systemCode": self.password,
                },
            )

            if res.status_code != 200:
                raise ConnectionError(
                    f"FusionSolar login failed: {res.status_code} — {res.text[:200]}"
                )

            data = res.json()
            if data.get("failCode") == 305:
                raise PermissionError("FusionSolar: Invalid credentials")
            if data.get("failCode") == 407:
                raise PermissionError("FusionSolar: Account locked (too many attempts)")

            # Token is in the Set-Cookie header as XSRF-TOKEN
            token = None
            for cookie_header in res.headers.get_list("set-cookie"):
                if "XSRF-TOKEN" in cookie_header:
                    token = cookie_header.split("XSRF-TOKEN=")[1].split(";")[0]
                    break

            if not token:
                raise ConnectionError("FusionSolar: No XSRF-TOKEN in response")

            self._token = token
            self._token_expires = datetime.now(timezone.utc)
            logger.info("FusionSolar: Authenticated successfully")

    async def _ensure_auth(self) -> None:
        """Re-authenticate if token is expired (30 min)."""
        if self._token is None or (
            self._token_expires
            and (datetime.now(timezone.utc) - self._token_expires).total_seconds() > 1500
        ):
            await self._authenticate()

    async def _request(self, endpoint: str, body: dict | None = None) -> dict:
        """Make authenticated request to FusionSolar API."""
        await self._ensure_auth()

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                f"{self.base_url}/{endpoint}",
                headers={"XSRF-TOKEN": self._token},
                cookies={"XSRF-TOKEN": self._token},
                json=body or {},
            )

            if res.status_code != 200:
                raise ConnectionError(f"FusionSolar API error: {res.status_code}")

            data = res.json()
            if not data.get("success", True) and data.get("failCode"):
                raise ConnectionError(
                    f"FusionSolar error {data['failCode']}: {data.get('message', 'Unknown')}"
                )

            return data

    # ─── Public API Methods ───────────────────────────────────────

    async def get_station_list(self) -> list[dict]:
        """Get all solar plants/stations under this account."""
        data = await self._request("getStationList", {"pageNo": 1, "pageSize": 100})
        return data.get("data", {}).get("list", [])

    async def get_station_realtime(self, station_code: str) -> dict:
        """Get real-time KPIs for a station (plant)."""
        data = await self._request(
            "getStationRealKpi",
            {"stationCodes": station_code},
        )
        stations = data.get("data", [])
        return stations[0] if stations else {}

    async def get_device_list(self, station_code: str) -> list[dict]:
        """Get all devices (inverters, meters, etc.) for a station."""
        data = await self._request(
            "getDevList",
            {"stationCodes": station_code},
        )
        return data.get("data", [])

    async def get_device_realtime(self, device_id: str, device_type_id: int) -> dict:
        """
        Get real-time data for a specific device.

        device_type_id:
          1 = String inverter
          38 = Residential inverter
          39 = Battery
          47 = Power sensor / meter
        """
        data = await self._request(
            "getDevRealKpi",
            {
                "devIds": device_id,
                "devTypeId": device_type_id,
            },
        )
        devices = data.get("data", [])
        return devices[0] if devices else {}

    async def get_device_history(
        self,
        device_id: str,
        device_type_id: int,
        collect_time: int,  # Unix timestamp in ms
    ) -> list[dict]:
        """Get 5-min resolution historical data for a device."""
        data = await self._request(
            "getDevHistoryKpi",
            {
                "devIds": device_id,
                "devTypeId": device_type_id,
                "collectTime": collect_time,
            },
        )
        return data.get("data", [])

    async def get_station_hourly(
        self, station_code: str, collect_time: int
    ) -> list[dict]:
        """Get hourly energy data for a station."""
        data = await self._request(
            "getKpiStationHour",
            {
                "stationCodes": station_code,
                "collectTime": collect_time,
            },
        )
        return data.get("data", [])

    async def test_connection(self) -> dict[str, Any]:
        """Test if credentials work and return station info."""
        try:
            await self._authenticate()
            stations = await self.get_station_list()
            return {
                "success": True,
                "stations_count": len(stations),
                "stations": [
                    {
                        "code": s.get("stationCode"),
                        "name": s.get("stationName"),
                        "capacity_kw": s.get("capacity"),
                        "address": s.get("stationAddr"),
                    }
                    for s in stations[:5]
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def disconnect(self) -> None:
        """Logout from FusionSolar."""
        if self._token:
            try:
                await self._request("logout")
            except Exception:
                pass
            self._token = None
