"""STEP 38: Control Orchestrator — Commands, Verifications, Audit, Snapshots, Locks

Revision ID: 038_control_orchestrator
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "038_control_orchestrator"
down_revision = "037_financial_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commands",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recommendation_id", sa.Integer(), nullable=True, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("failure_reason", sa.String(100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("trace_id", sa.String(100), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rollback_payload_json", sa.Text(), nullable=True),
        sa.Column("is_rollback", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "command_verifications",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("command_id", sa.Integer(), sa.ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("tolerance", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="VERIFIED"),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "command_audit",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("command_id", sa.Integer(), sa.ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="SYSTEM"),
        sa.Column("old_status", sa.String(30), nullable=True),
        sa.Column("new_status", sa.String(30), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "control_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("command_id", sa.Integer(), sa.ForeignKey("commands.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("battery_soc", sa.Float(), nullable=True),
        sa.Column("solar_power_kw", sa.Float(), nullable=True),
        sa.Column("load_power_kw", sa.Float(), nullable=True),
        sa.Column("grid_price", sa.Float(), nullable=True),
        sa.Column("device_status", sa.String(20), nullable=True),
        sa.Column("forecast_version", sa.String(50), nullable=True),
        sa.Column("safety_policy_version", sa.String(20), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "control_locks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("command_id", sa.Integer(), sa.ForeignKey("commands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("control_locks")
    op.drop_table("control_snapshots")
    op.drop_table("command_audit")
    op.drop_table("command_verifications")
    op.drop_table("commands")
