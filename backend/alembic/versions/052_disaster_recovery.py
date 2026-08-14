"""STEP 52: Disaster Recovery — Targets, Drills, Events, Checklists

Revision ID: 052_disaster_recovery
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "052_disaster_recovery"
down_revision = "051_performance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("recovery_targets",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("service", sa.String(50), nullable=False, unique=True),
        sa.Column("rpo_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("rto_minutes", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="HIGH"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("recovery_drills",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("scenario", sa.String(100), nullable=False),
        sa.Column("environment", sa.String(20), nullable=False, server_default="staging"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PLANNED"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detection_time_minutes", sa.Float(), nullable=True),
        sa.Column("restore_time_minutes", sa.Float(), nullable=True),
        sa.Column("validation_time_minutes", sa.Float(), nullable=True),
        sa.Column("total_recovery_minutes", sa.Float(), nullable=True),
        sa.Column("data_loss_minutes", sa.Float(), nullable=True),
        sa.Column("rto_met", sa.Boolean(), nullable=True),
        sa.Column("rpo_met", sa.Boolean(), nullable=True),
        sa.Column("issues_found", sa.Text(), nullable=True),
        sa.Column("executed_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("recovery_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("drill_id", sa.Integer(), sa.ForeignKey("recovery_drills.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(100), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("recovery_checklists",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("drill_id", sa.Integer(), sa.ForeignKey("recovery_drills.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("item", sa.String(200), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("checked_by", sa.String(100), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recovery_checklists")
    op.drop_table("recovery_events")
    op.drop_table("recovery_drills")
    op.drop_table("recovery_targets")
