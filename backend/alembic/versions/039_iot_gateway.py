"""STEP 39: IoT Gateway — Gateways, Processed Messages, Dead Letter Queue

Revision ID: 039_iot_gateway
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "039_iot_gateway"
down_revision = "038_control_orchestrator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gateways",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("gateway_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("firmware_version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PROVISIONING"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("connected_devices", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("signal_quality", sa.Float(), nullable=True),
        sa.Column("heartbeat_interval_sec", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("offline_threshold_sec", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("buffer_limit", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("telemetry_batch_size", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "processed_messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("message_id", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", sa.String(20), nullable=False, server_default="PROCESSED"),
    )

    op.create_table(
        "dead_letter_queue",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), nullable=True, index=True),
        sa.Column("factory_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("dead_letter_queue")
    op.drop_table("processed_messages")
    op.drop_table("gateways")
