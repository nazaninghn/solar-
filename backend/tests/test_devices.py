import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.devices.battery.simulator import SimulatorBattery
from app.devices.inverter.simulator import SimulatorInverter
from app.devices.scenario import set_scenario
from app.devices.validation import is_timestamp_plausible
from app.energy.balance import check_energy_balance
from app.main import app
from app.models.energy_reading import EnergyReading

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_admin() -> str:
    email = _unique_email("device-test-admin")

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Device Test Admin",
            "organization_name": "Device Test Org",
        },
    )

    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "TestPass123!"}
    )

    return login.json()["access_token"]


def _create_factory_and_device(admin_token: str) -> tuple[int, int, str]:
    headers = {"Authorization": f"Bearer {admin_token}"}

    factory = client.post(
        "/api/v1/factories", json={"name": "Device Test Factory"}, headers=headers
    ).json()

    device = client.post(
        f"/api/v1/factories/{factory['id']}/devices",
        json={
            "name": "Pytest Inverter",
            "device_type": "INVERTER",
            "connection_type": "API",
        },
        headers=headers,
    ).json()

    return factory["id"], device["id"], device["device_key"]


# --- Energy balance (26.21-26.22) ---


def test_energy_balance_within_tolerance_passes():
    reading = EnergyReading(
        solar_generation_kwh=100,
        grid_import_kwh=0,
        battery_discharge_kwh=0,
        consumption_kwh=95,
        grid_export_kwh=5,
        battery_charge_kwh=0,
    )
    assert check_energy_balance(reading) is None


def test_energy_balance_beyond_tolerance_flags():
    reading = EnergyReading(
        solar_generation_kwh=900,
        grid_import_kwh=0,
        battery_discharge_kwh=0,
        consumption_kwh=0,
        grid_export_kwh=0,
        battery_charge_kwh=0,
    )
    violation = check_energy_balance(reading)
    assert violation is not None
    assert violation["diff_kwh"] == 900


# --- Timestamp validation (26.35) ---


def test_timestamp_within_window_is_plausible():
    assert is_timestamp_plausible(datetime.now(timezone.utc)) is True


def test_timestamp_far_in_past_is_implausible():
    assert is_timestamp_plausible(datetime(2020, 1, 1, tzinfo=timezone.utc)) is False


def test_timestamp_far_in_future_is_implausible():
    far_future = datetime.now(timezone.utc) + timedelta(days=30)
    assert is_timestamp_plausible(far_future) is False


# --- Scenario-based simulator (26.37) ---


def test_sunny_scenario_raises_inverter_output():
    async def run():
        set_scenario("SUNNY")
        data = await SimulatorInverter().read_data()
        set_scenario("NORMAL")
        return data

    data = asyncio.run(run())
    assert data["power_kw"] >= 4000


def test_cloudy_scenario_lowers_inverter_output():
    async def run():
        set_scenario("CLOUDY")
        data = await SimulatorInverter().read_data()
        set_scenario("NORMAL")
        return data

    data = asyncio.run(run())
    assert data["power_kw"] <= 1200


def test_battery_low_scenario_forces_low_soc():
    async def run():
        set_scenario("BATTERY_LOW")
        data = await SimulatorBattery().read_data()
        set_scenario("NORMAL")
        return data

    data = asyncio.run(run())
    assert data["soc_percent"] < 10


def test_device_offline_scenario_raises():
    async def run():
        set_scenario("DEVICE_OFFLINE")
        try:
            await SimulatorInverter().read_data()
            raised = False
        except ConnectionError:
            raised = True
        set_scenario("NORMAL")
        return raised

    assert asyncio.run(run()) is True


# --- Telemetry ingestion (26.14-26.16, 26.34-26.36), live against the app ---


def test_telemetry_requires_device_key():
    admin_token = _register_admin()
    _, device_id, _ = _create_factory_and_device(admin_token)

    response = client.post(
        f"/api/v1/devices/{device_id}/telemetry",
        json={"timestamp": datetime.now(timezone.utc).isoformat(), "power_kw": 100},
    )
    assert response.status_code == 401


def test_telemetry_rejects_wrong_device_key():
    admin_token = _register_admin()
    _, device_id, _ = _create_factory_and_device(admin_token)

    response = client.post(
        f"/api/v1/devices/{device_id}/telemetry",
        json={"timestamp": datetime.now(timezone.utc).isoformat(), "power_kw": 100},
        headers={"X-Device-Key": "not-the-real-key"},
    )
    assert response.status_code == 401


def test_telemetry_ingestion_succeeds_and_replay_is_deduplicated():
    admin_token = _register_admin()
    _, device_id, device_key = _create_factory_and_device(admin_token)

    timestamp = datetime.now(timezone.utc).isoformat()
    headers = {"X-Device-Key": device_key}
    payload = {"timestamp": timestamp, "power_kw": 4280, "energy_kwh": 1850}

    first = client.post(
        f"/api/v1/devices/{device_id}/telemetry", json=payload, headers=headers
    )
    assert first.status_code == 200
    assert first.json()["recorded"] is True

    replay = client.post(
        f"/api/v1/devices/{device_id}/telemetry", json=payload, headers=headers
    )
    assert replay.status_code == 200
    assert replay.json()["duplicate"] is True
    assert replay.json()["id"] == first.json()["id"]


def test_telemetry_rejects_implausible_timestamp():
    admin_token = _register_admin()
    _, device_id, device_key = _create_factory_and_device(admin_token)

    response = client.post(
        f"/api/v1/devices/{device_id}/telemetry",
        json={"timestamp": "2020-01-01T00:00:00Z", "power_kw": 100},
        headers={"X-Device-Key": device_key},
    )
    assert response.status_code == 400


def test_telemetry_rejects_negative_inverter_power():
    admin_token = _register_admin()
    _, device_id, device_key = _create_factory_and_device(admin_token)

    response = client.post(
        f"/api/v1/devices/{device_id}/telemetry",
        json={"timestamp": datetime.now(timezone.utc).isoformat(), "power_kw": -50},
        headers={"X-Device-Key": device_key},
    )
    assert response.status_code == 400


def test_telemetry_device_key_scoped_to_its_own_device():
    admin_token = _register_admin()
    factory_id, device_id, device_key = _create_factory_and_device(admin_token)

    other_device = client.post(
        f"/api/v1/factories/{factory_id}/devices",
        json={
            "name": "Second Pytest Device",
            "device_type": "BATTERY",
            "connection_type": "API",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()

    response = client.post(
        f"/api/v1/devices/{other_device['id']}/telemetry",
        json={"timestamp": datetime.now(timezone.utc).isoformat(), "soc_percent": 50},
        headers={"X-Device-Key": device_key},
    )
    assert response.status_code == 401
