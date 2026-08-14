from datetime import datetime

from pydantic import BaseModel


class LegalHoldCreate(BaseModel):
    resource_type: str
    resource_id: int
    reason: str


class LegalHoldResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: int
    reason: str
    created_by: int | None
    created_at: datetime
    released_by: int | None
    released_at: datetime | None
    model_config = {"from_attributes": True}


class VendorCreate(BaseModel):
    name: str
    purpose: str
    data_access_description: str
    risk_tier: str = "MEDIUM"
    contract_reference: str | None = None
    dpa_signed: bool = False


class VendorResponse(BaseModel):
    id: int
    name: str
    purpose: str
    data_access_description: str
    risk_tier: str
    status: str
    contract_reference: str | None
    dpa_signed: bool
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}
