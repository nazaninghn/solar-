"""STEP 50: Data Integrity — Quality Records, Reconciliation, Anomalies, Corrections

Revision ID: 050_data_integrity
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "050_data_integrity"
down_revision = "049_monitoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("data_quality_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_count", sa.Integer(), nullable=False),
        sa.Column("received_count", sa.Integer(), nullable=False),
        sa.Column("invalid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("late_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("device_id", "metric", "period_start", name="uq_dq_record"),
    )
    op.create_table("energy_reconciliations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generation_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consumption_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_export_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_charge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_discharge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("difference_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tolerance_kwh", sa.Float(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(20), nullable=False, server_default="MATCHED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("data_anomalies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("detected_value", sa.Float(), nullable=True),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DETECTED"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("data_corrections",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_value", sa.Float(), nullable=False),
        sa.Column("new_value", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("corrected_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("data_corrections")
    op.drop_table("data_anomalies")
    op.drop_table("energy_reconciliations")
    op.drop_table("data_quality_records")
