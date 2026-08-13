from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.access_control import can_access_factory
from app.auth.audit import log_audit_action
from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_FACTORY_SETTINGS
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.schemas.factory import FactoryCreate, FactoryResponse, FactoryUpdate

router = APIRouter(
    prefix="/api/v1/factories",
    tags=["Factories"],
)


@router.get("", response_model=list[FactoryResponse])
def list_factories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Step 24 (24.7): a non-admin user may be scoped to a subset of their
    # company's factories via user_factory_access — this list must not
    # leak factories the caller can't individually open. Also doubles as
    # the "which factories can I switch to" list (24.32) for every role,
    # since admins already see their full company here via
    # can_access_factory's short-circuit.
    org_factories = db.scalars(
        select(Factory).where(Factory.organization_id == current_user.organization_id)
    ).all()

    return [
        factory
        for factory in org_factories
        if can_access_factory(db, current_user, factory)
    ]


@router.post("", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
def create_factory(
    data: FactoryCreate,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_FACTORY_SETTINGS)),
    db: Session = Depends(get_db),
):
    factory = Factory(
        organization_id=current_user.organization_id,
        **data.model_dump(exclude_unset=True),
    )

    db.add(factory)
    db.flush()

    log_audit_action(
        db, current_user, "CREATE_FACTORY", "Factory",
        resource_id=factory.id, request=request,
    )
    db.commit()
    db.refresh(factory)

    return factory


@router.get("/{factory_id}", response_model=FactoryResponse)
def get_factory(factory: Factory = Depends(get_accessible_factory)):
    return factory


@router.patch("/{factory_id}", response_model=FactoryResponse)
def update_factory(
    data: FactoryUpdate,
    request: Request,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_FACTORY_SETTINGS)),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(factory, field, value)

    log_audit_action(
        db, current_user, "UPDATE_FACTORY", "Factory",
        resource_id=factory.id, request=request,
    )
    db.commit()
    db.refresh(factory)

    return factory


@router.delete("/{factory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_factory(
    request: Request,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_FACTORY_SETTINGS)),
    db: Session = Depends(get_db),
):
    factory_id = factory.id
    db.delete(factory)

    log_audit_action(
        db, current_user, "DELETE_FACTORY", "Factory",
        resource_id=factory_id, request=request,
    )
    db.commit()
