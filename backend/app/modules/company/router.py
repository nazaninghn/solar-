from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.audit import log_audit_action
from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_COMPANY_SETTINGS, MANAGE_USERS
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.company.schemas import (
    AuditLogResponse,
    CompanyUserCreate,
    CompanyUserResponse,
    CompanyUserUpdate,
    FactoryAccessGrant,
    OrganizationResponse,
    OrganizationUpdate,
    UserFactoryAccessResponse,
)
from app.modules.company.service import (
    create_company_user,
    deactivate_company_user,
    grant_factory_access,
    list_audit_log,
    list_company_users,
    list_user_factory_access,
    revoke_factory_access,
    update_company_user,
    update_organization,
)
from app.modules.performance.quota_enforcement import enforce_user_quota

router = APIRouter(
    prefix="/api/v1/company",
    tags=["Company"],
)


def _get_company_user(
    user_id: int, current_user: User, db: Session
) -> User:
    """Same 404-for-cross-tenant / scoped-to-your-own-company pattern as
    get_accessible_factory — a user from another company should never be
    able to tell (via status code) whether a given user_id exists."""
    user = db.get(User, user_id)

    if user is None or user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get("", response_model=OrganizationResponse)
def get_company(current_user: User = Depends(get_current_user)):
    return current_user.organization


@router.patch("", response_model=OrganizationResponse)
def update_company(
    data: OrganizationUpdate,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_COMPANY_SETTINGS)),
    db: Session = Depends(get_db),
):
    organization = update_organization(db, current_user.organization, data)

    log_audit_action(
        db, current_user, "UPDATE_COMPANY_SETTINGS", "Organization",
        resource_id=organization.id, request=request,
    )
    db.commit()

    return organization


@router.get("/users", response_model=list[CompanyUserResponse])
def list_users(
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    return list_company_users(db, current_user.organization_id)


@router.post(
    "/users",
    response_model=CompanyUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: CompanyUserCreate,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    enforce_user_quota(db, current_user.organization_id)

    try:
        user = create_company_user(db, current_user.organization_id, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    log_audit_action(
        db, current_user, "CREATE_USER", "User",
        resource_id=user.id, request=request,
    )
    db.commit()

    return user


@router.patch("/users/{user_id}", response_model=CompanyUserResponse)
def update_user(
    user_id: int,
    data: CompanyUserUpdate,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    user = _get_company_user(user_id, current_user, db)

    try:
        updated_user = update_company_user(db, user, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    log_audit_action(
        db, current_user, "UPDATE_USER", "User",
        resource_id=updated_user.id, request=request,
    )
    db.commit()

    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    user = _get_company_user(user_id, current_user, db)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    deactivate_company_user(db, user)

    log_audit_action(
        db, current_user, "DEACTIVATE_USER", "User",
        resource_id=user.id, request=request,
    )
    db.commit()


@router.get(
    "/users/{user_id}/factories", response_model=list[UserFactoryAccessResponse]
)
def get_user_factory_access(
    user_id: int,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    user = _get_company_user(user_id, current_user, db)

    return [
        UserFactoryAccessResponse(factory_id=factory.id, factory_name=factory.name)
        for factory in list_user_factory_access(db, user.id)
    ]


@router.post(
    "/users/{user_id}/factories",
    status_code=status.HTTP_204_NO_CONTENT,
)
def add_user_factory_access(
    user_id: int,
    data: FactoryAccessGrant,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    user = _get_company_user(user_id, current_user, db)
    factory = db.get(Factory, data.factory_id)

    if factory is None or factory.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found",
        )

    grant_factory_access(db, user, factory)

    log_audit_action(
        db, current_user, "GRANT_FACTORY_ACCESS", "UserFactoryAccess",
        resource_id=user.id, request=request,
    )
    db.commit()


@router.delete(
    "/users/{user_id}/factories/{factory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_factory_access(
    user_id: int,
    factory_id: int,
    request: Request,
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    user = _get_company_user(user_id, current_user, db)
    revoke_factory_access(db, user.id, factory_id)

    log_audit_action(
        db, current_user, "REVOKE_FACTORY_ACCESS", "UserFactoryAccess",
        resource_id=user.id, request=request,
    )
    db.commit()


@router.get("/audit-log", response_model=list[AuditLogResponse])
def get_audit_log(
    current_user: User = Depends(require_permission(MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    return list_audit_log(db, current_user.organization_id)
