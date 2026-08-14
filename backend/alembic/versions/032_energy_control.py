"""STEP 32: Energy Actions and Command Queue tables

Revision ID: 032_energy_control
Revises: 
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa


revision = "032_energy_control"
down_revision = None  # Will be set by alembic autogenerate
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "energy_actions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_power_kw", sa.Float(), nullable=True),
        sa.Column("target_energy_kwh", sa.Float(), nullable=True),
        sa.Column("target_soc", sa.Float(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "command_queue",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("action_id", sa.Integer(), sa.ForeignKey("energy_actions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("command_type", sa.String(50), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("command_queue")
    op.drop_table("energy_actions")
