from datetime import date as date_type

from pydantic import BaseModel


class IntegrationFactoryEnergySummary(BaseModel):
    factory_id: int
    factory_name: str
    latest_date: date_type | None
    solar_kwh: float | None
    consumption_kwh: float | None
    grid_import_kwh: float | None
    grid_export_kwh: float | None


class IntegrationEnergySummaryResponse(BaseModel):
    organization_id: int
    organization_name: str
    factories: list[IntegrationFactoryEnergySummary]
