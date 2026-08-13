from pydantic import BaseModel


class NotificationPreferenceResponse(BaseModel):
    battery_alerts: bool
    price_alerts: bool
    weather_alerts: bool
    energy_alerts: bool
    financial_alerts: bool
    system_alerts: bool
    email_enabled: bool
    sms_enabled: bool
    dashboard_enabled: bool

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    battery_alerts: bool | None = None
    price_alerts: bool | None = None
    weather_alerts: bool | None = None
    energy_alerts: bool | None = None
    financial_alerts: bool | None = None
    system_alerts: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    dashboard_enabled: bool | None = None
