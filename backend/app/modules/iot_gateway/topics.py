"""
STEP 39.6-39.7: MQTT Topic Design & Versioning.

Centralized topic generation — all MQTT topic patterns in one place.
"""

MQTT_VERSION = "v1"
ENVIRONMENT = "production"  # Override from env var


def telemetry_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/telemetry"


def status_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/status"


def command_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/command"


def ack_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/ack"


def event_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/event"


def heartbeat_topic(factory_id: str, device_id: str) -> str:
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}/heartbeat"


def factory_wildcard(factory_id: str) -> str:
    """Subscribe to all devices in a factory."""
    return f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/+/#"


def device_acl(factory_id: str, device_id: str) -> dict:
    """39.28: ACL rules for a specific device."""
    base = f"solarflow/{MQTT_VERSION}/factory/{factory_id}/device/{device_id}"
    return {
        "publish": [f"{base}/telemetry", f"{base}/status", f"{base}/ack", f"{base}/heartbeat"],
        "subscribe": [f"{base}/command"],
    }
