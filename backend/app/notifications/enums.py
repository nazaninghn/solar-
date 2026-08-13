from enum import Enum


class AlertType(str, Enum):
    ENERGY = "ENERGY"
    BATTERY = "BATTERY"
    PRICE = "PRICE"
    WEATHER = "WEATHER"
    FINANCIAL = "FINANCIAL"
    SYSTEM = "SYSTEM"
    FORECAST = "FORECAST"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


class AlertStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
