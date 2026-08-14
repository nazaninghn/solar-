"""
STEP 36: Optimization Service.

Orchestrates recommendation generation, deduplication, approval, and lifecycle.
"""

import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.optimization.models import (
    REC_APPROVED,
    REC_CANCELLED,
    REC_COMPLETED,
    REC_EXPIRED,
    REC_FAILED,
    REC_PENDING,
    REC_REJECTED,
    RecommendationHistory,
    SmartRecommendation,
)
from app.modules.optimization.rule_engine import generate_recommendations


def generate_factory_recommendations(
    db: Session,
    factory_id: int,
    solar_forecast_kwh: float = 3500.0,
    load_forecast_kwh: float = 4500.0,
    battery_soc: float = 55.0,
    grid_price_current: float = 0.18,
    grid_price_peak: float = 0.32,
    grid_price_offpeak: float = 0.12,
    export_price: float = 0.15,
) -> list[SmartRecommendation]:
    """Generate and store new recommendations (with dedup)."""
    raw_recs = generate_recommendations(
        factory_id=factory_id,
        solar_forecast_kwh=solar_forecast_kwh,
        load_forecast_kwh=load_forecast_kwh,
        battery_soc=battery_soc,
        grid_price_current=grid_price_current,
        grid_price_peak=grid_price_peak,
        grid_price_offpeak=grid_price_offpeak,
        export_price=export_price,
    )

    now = datetime.now(timezone.utc)
    created: list[SmartRecommendation] = []

    for rec_data in raw_recs:
        # 36.24: Deduplication
        dedup_key = _make_dedup_key(factory_id, rec_data["type"], rec_data.get("start_time"))

        existing = (
            db.query(SmartRecommendation)
            .filter(
                SmartRecommendation.dedup_key == dedup_key,
                SmartRecommendation.status.in_([REC_PENDING, REC_APPROVED]),
            )
            .first()
        )
        if existing:
            continue  # Skip duplicate

        rec = SmartRecommendation(
            factory_id=factory_id,
            type=rec_data["type"],
            title=rec_data["title"],
            description=rec_data["description"],
            status=REC_PENDING,
            priority=rec_data["priority"],
            confidence=rec_data["confidence"],
            score=rec_data["score"],
            expected_savings=rec_data["expected_savings"],
            expected_revenue=rec_data.get("expected_revenue", 0),
            savings_lower=rec_data.get("savings_lower"),
            savings_upper=rec_data.get("savings_upper"),
            start_time=rec_data.get("start_time"),
            end_time=rec_data.get("end_time"),
            expires_at=rec_data.get("end_time"),
            reasoning=rec_data.get("reasoning"),
            reason_codes_json=rec_data.get("reason_codes_json"),
            model_version=rec_data.get("model_version"),
            rules_version=rec_data.get("rules_version"),
            risk_score=rec_data.get("risk_score", 0),
            dedup_key=dedup_key,
            created_at=now,
        )
        db.add(rec)
        created.append(rec)

    if created:
        db.commit()
        for r in created:
            db.refresh(r)

    return created


def get_recommendations(db: Session, factory_id: int) -> list[SmartRecommendation]:
    """Get all active recommendations sorted by score."""
    return (
        db.query(SmartRecommendation)
        .filter(SmartRecommendation.factory_id == factory_id)
        .order_by(SmartRecommendation.score.desc())
        .limit(50)
        .all()
    )


def get_recommendation(db: Session, recommendation_id: int, factory_id: int) -> SmartRecommendation:
    rec = (
        db.query(SmartRecommendation)
        .filter(
            SmartRecommendation.id == recommendation_id,
            SmartRecommendation.factory_id == factory_id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    return rec


def approve_recommendation(
    db: Session, recommendation_id: int, factory_id: int, user: User
) -> SmartRecommendation:
    """36.26: Approve with lifecycle and audit."""
    rec = get_recommendation(db, recommendation_id, factory_id)

    if rec.status != REC_PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve in status '{rec.status}'.")

    # Check expiry (36.34)
    if rec.expires_at and rec.expires_at < datetime.now(timezone.utc):
        rec.status = REC_EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="Recommendation has expired.")

    old_status = rec.status
    rec.status = REC_APPROVED
    rec.approved_by = user.id
    rec.approved_at = datetime.now(timezone.utc)

    _add_history(db, rec.id, old_status, REC_APPROVED, user.id, "Approved")
    db.commit()
    db.refresh(rec)
    return rec


def reject_recommendation(
    db: Session, recommendation_id: int, factory_id: int, user: User, reason: str | None = None
) -> SmartRecommendation:
    rec = get_recommendation(db, recommendation_id, factory_id)
    if rec.status != REC_PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot reject in status '{rec.status}'.")

    old_status = rec.status
    rec.status = REC_REJECTED
    _add_history(db, rec.id, old_status, REC_REJECTED, user.id, reason)
    db.commit()
    db.refresh(rec)
    return rec


def cancel_recommendation(
    db: Session, recommendation_id: int, factory_id: int, user: User
) -> SmartRecommendation:
    rec = get_recommendation(db, recommendation_id, factory_id)
    if rec.status in (REC_COMPLETED, REC_FAILED, REC_EXPIRED):
        raise HTTPException(status_code=400, detail=f"Cannot cancel in status '{rec.status}'.")

    old_status = rec.status
    rec.status = REC_CANCELLED
    _add_history(db, rec.id, old_status, REC_CANCELLED, user.id, "Cancelled by user")
    db.commit()
    db.refresh(rec)
    return rec


def _make_dedup_key(factory_id: int, rec_type: str, start_time: datetime | None) -> str:
    """36.24: Create dedup key."""
    time_bucket = ""
    if start_time:
        time_bucket = start_time.strftime("%Y-%m-%d-%H")
    raw = f"{factory_id}:{rec_type}:{time_bucket}"
    return hashlib.md5(raw.encode()).hexdigest()


def _add_history(
    db: Session, rec_id: int, old: str, new: str, user_id: int | None, reason: str | None
) -> None:
    db.add(RecommendationHistory(
        recommendation_id=rec_id,
        status=new,
        changed_by=user_id,
        old_value=old,
        new_value=new,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    ))
