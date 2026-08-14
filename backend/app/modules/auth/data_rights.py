"""
STEP 79.36-79.40: self-service data subject rights (export + deletion/
anonymization). Nothing like this existed before — the closest prior
art was deactivate_company_user (app/modules/company/service.py), an
ADMIN action against someone else's account, not a user's own
self-service request, and it never touched the user's PII (email/name
stay as-is, only is_active flips).

Scoped to what a user in this B2B product actually "owns": their
account profile, their own audit trail entries, and their factory
access grants. Shared business data (factories, energy readings,
financial records, recommendations) belongs to the organization, not
to any one user, and is deliberately untouched by an individual
account deletion — a company's factory data doesn't stop existing
because one employee left.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.audit_log import AuditLog
from app.models.recommendation_audit_log import RecommendationAuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_factory_access import UserFactoryAccess
from app.modules.compliance.service import is_organization_on_hold


class LegalHoldBlockError(ValueError):
    pass


class IdentityVerificationError(ValueError):
    pass


class LastAdminError(ValueError):
    pass


def export_own_data(db: Session, user: User) -> dict:
    """79.36, 79.38: JSON export of everything tied to this specific
    user_id — not a full company data dump, which is a different
    (organization-level, admin-only) concern."""
    factory_access = db.scalars(
        select(UserFactoryAccess).where(UserFactoryAccess.user_id == user.id)
    ).all()

    audit_entries = db.scalars(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(500)
    ).all()

    recommendation_decisions = db.scalars(
        select(RecommendationAuditLog)
        .where(RecommendationAuditLog.user_id == user.id)
        .order_by(RecommendationAuditLog.timestamp.desc())
        .limit(500)
    ).all()

    return {
        "account": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        },
        "organization": {
            "id": user.organization_id,
            "name": user.organization.name,
        },
        "factory_access": [
            {"factory_id": fa.factory_id, "granted_at": fa.created_at.isoformat()}
            for fa in factory_access
        ],
        "audit_trail": [
            {
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in audit_entries
        ],
        "recommendation_decisions": [
            {
                "recommendation_id": entry.recommendation_id,
                "action": entry.action,
                "reason": entry.reason,
                "timestamp": entry.timestamp.isoformat(),
            }
            for entry in recommendation_decisions
        ],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def delete_own_account(db: Session, user: User, password: str) -> None:
    """
    79.37: identity verification (re-enter password) before a
    destructive self-service request. 79.39-79.40: anonymize rather
    than hard-delete — a hard DELETE would cascade-orphan or corrupt
    every AuditLog/RecommendationAuditLog row this user is referenced
    from (both FKs are ondelete="CASCADE"), destroying the very audit
    trail 79.26 says must survive the person being audited. PII is
    scrubbed from the row itself instead; the audit rows keep a valid,
    now-anonymous user_id to point at.
    """
    if not verify_password(password, user.hashed_password):
        raise IdentityVerificationError("Incorrect password")

    # 79.33: a litigation hold on this organization suspends identity-
    # scrubbing too, not just bulk retention purges — a hold typically
    # covers preserving who-did-what for the custodians involved, and
    # anonymizing a user's name/email is exactly the kind of change
    # that would undermine that. Blocked in favor of routing through an
    # admin/legal channel instead of a silent self-service action.
    if is_organization_on_hold(db, user.organization_id):
        raise LegalHoldBlockError(
            "This organization is under legal hold — account deletion is "
            "suspended. Contact your administrator."
        )

    if user.role in ("COMPANY_ADMIN", "SUPER_ADMIN"):
        other_active_admins = db.scalar(
            select(User.id).where(
                User.organization_id == user.organization_id,
                User.role.in_(("COMPANY_ADMIN", "SUPER_ADMIN")),
                User.is_active.is_(True),
                User.id != user.id,
            )
        )
        if other_active_admins is None:
            raise LastAdminError(
                "Cannot delete the only active admin for this organization — "
                "assign another admin first"
            )

    now = datetime.now(timezone.utc)

    db.add(
        AuditLog(
            user_id=user.id,
            organization_id=user.organization_id,
            action="ACCOUNT_SELF_DELETION",
            resource_type="user",
            resource_id=user.id,
            created_at=now,
        )
    )

    user.email = f"deleted-user-{user.id}-{uuid.uuid4().hex[:8]}@anonymized.solarflow.internal"
    user.full_name = "Deleted User"
    user.hashed_password = hash_password(uuid.uuid4().hex)
    user.is_active = False

    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )

    db.commit()
