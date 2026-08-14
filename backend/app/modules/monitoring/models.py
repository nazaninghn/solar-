"""
STEP 49: Production Monitoring Models.

Incidents, Incident Events, Alert Rules, Deployments, Postmortems.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MonitoringIncident(Base):
    """49.29: Production incidents."""
    __tablename__ = "monitoring_incidents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARNING")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    service: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IncidentEvent(Base):
    """49.34: Incident timeline events."""
    __tablename__ = "incident_events"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MonitoringAlertRule(Base):
    """49.52: Configurable alert rules for metrics."""
    __tablename__ = "monitoring_alert_rules"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(10), nullable=False)  # >, <, >=, <=, ==
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="WARNING")
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DeploymentRecord(Base):
    """49.37: Deployment tracking for correlation."""
    __tablename__ = "deployment_records"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="production")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DEPLOYED")
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deployed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rollback_of: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IncidentPostmortem(Base):
    """49.60: Incident postmortem."""
    __tablename__ = "incident_postmortems"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    customer_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    preventive_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# STEP 77.66-77.68: the table above existed with no workflow around it
# — no way to create/update one, and "preventive_actions" was a single
# free-text blob with no owner/deadline/status to actually track. This
# is the missing corrective-action tracking, one row per action item
# rather than one paragraph covering all of them.
CORRECTIVE_ACTION_STATUSES = ("OPEN", "IN_PROGRESS", "DONE")


class PostmortemCorrectiveAction(Base):
    __tablename__ = "postmortem_corrective_actions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    postmortem_id: Mapped[int] = mapped_column(
        ForeignKey("incident_postmortems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Free-text, matching IncidentPostmortem.owner's own shape above —
    # not every "owner" of a corrective action is necessarily a user
    # account in this system (could be "Platform Team", a vendor, etc).
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
