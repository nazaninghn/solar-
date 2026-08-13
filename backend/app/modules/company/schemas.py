from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str | None
    email: str | None
    phone: str | None
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    currency: str | None = None
    timezone: str | None = None


class CompanyUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime


class CompanyUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: str


class CompanyUserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class FactoryAccessGrant(BaseModel):
    factory_id: int


class UserFactoryAccessResponse(BaseModel):
    model_config = {"from_attributes": True}

    factory_id: int
    factory_name: str


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: int | None
    ip_address: str | None
    created_at: datetime
