"""Failure prediction — risk assessments and failure event log

Revision ID: 053_failure_prediction
Revises: 5c46123306ad
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "053_failure_prediction"
down_revision = "5c46123306ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "failure_risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("ml_status", sa.String(30), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("failure_probability", sa.Float(), nullable=True),
        sa.Column("horizon_minutes", sa.Integer(), nullable=True),
        sa.Column("fault_type", sa.String(50), nullable=True),
        sa.Column("fault_type_confidence", sa.Float(), nullable=True),
        sa.Column("irradiance_source", sa.String(20), nullable=True),
        sa.Column("imputed_inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("indicators", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("top_reason", sa.String(50), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("days_to_threshold", sa.Float(), nullable=True),
        sa.Column("data_points", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_failure_risk_device_assessed",
        "failure_risk_assessments",
        ["device_id", "assessed_at"],
    )

    op.create_table(
        "failure_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reported_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("failure_events")
    op.drop_index("ix_failure_risk_device_assessed", table_name="failure_risk_assessments")
    op.drop_table("failure_risk_assessments")
