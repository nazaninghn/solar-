"""
82: the one read-only, org-scoped endpoint that actually consumes the
APIKey model — proves the service-identity credential works end to end.
Deliberately minimal (one endpoint, read-only, no write path) since an
API key has no role/permission concept of its own to gate a broader
surface with; expand only if a real external-integration need shows up.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.energy_daily import EnergyDaily
from app.models.factory import Factory
from app.models.organization import Organization
from app.modules.admin.api_key_auth import get_organization_from_api_key
from app.modules.admin.integrations_schemas import (
    IntegrationEnergySummaryResponse,
    IntegrationFactoryEnergySummary,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["External Integrations"])


@router.get("/energy-summary", response_model=IntegrationEnergySummaryResponse)
def get_energy_summary(
    organization: Organization = Depends(get_organization_from_api_key),
    db: Session = Depends(get_db),
):
    factories = db.scalars(
        select(Factory).where(Factory.organization_id == organization.id)
    ).all()

    entries = []
    for factory in factories:
        latest = db.scalar(
            select(EnergyDaily)
            .where(EnergyDaily.factory_id == factory.id)
            .order_by(EnergyDaily.date.desc())
            .limit(1)
        )
        entries.append(
            IntegrationFactoryEnergySummary(
                factory_id=factory.id,
                factory_name=factory.name,
                latest_date=latest.date if latest else None,
                solar_kwh=latest.solar_kwh if latest else None,
                consumption_kwh=latest.consumption_kwh if latest else None,
                grid_import_kwh=latest.grid_import_kwh if latest else None,
                grid_export_kwh=latest.grid_export_kwh if latest else None,
            )
        )

    return IntegrationEnergySummaryResponse(
        organization_id=organization.id,
        organization_name=organization.name,
        factories=entries,
    )
