"""STEP 34: Data Pipeline — Raw, Aggregations, Daily Summary, Quality, Metric Catalog

Revision ID: 034_data_pipeline
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "034_data_pipeline"
down_revision = "033_device_gateway"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_telemetry",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("message_id", sa.String(100), nullable=True, index=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ingestion_status", sa.String(20), nullable=False, server_default="RECEIVED"),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "metric_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("key", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("data_type", sa.String(20), nullable=False, server_default="float"),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("aggregation", sa.String(20), nullable=False, server_default="avg"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.create_table(
        "telemetry_5m",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("min_value", sa.Float(), nullable=False),
        sa.Column("max_value", sa.Float(), nullable=False),
        sa.Column("avg_value", sa.Float(), nullable=False),
        sa.Column("sum_value", sa.Float(), nullable=False),
        sa.Column("last_value", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_summary", sa.String(20), nullable=False, server_default="GOOD"),
        sa.UniqueConstraint("factory_id", "device_id", "metric", "bucket_start", name="uq_telemetry_5m"),
    )

    op.create_table(
        "telemetry_hourly",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("min_value", sa.Float(), nullable=False),
        sa.Column("max_value", sa.Float(), nullable=False),
        sa.Column("avg_value", sa.Float(), nullable=False),
        sa.Column("sum_value", sa.Float(), nullable=False),
        sa.Column("last_value", sa.Float(), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_summary", sa.String(20), nullable=False, server_default="GOOD"),
        sa.UniqueConstraint("factory_id", "device_id", "metric", "bucket_start", name="uq_telemetry_hourly"),
    )

    op.create_table(
        "daily_energy_summary",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False, index=True),
        sa.Column("solar_generation_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("factory_consumption_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_export_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_charge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_discharge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_savings", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peak_power_kw", sa.Float(), nullable=True),
        sa.Column("peak_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=False, server_default="GOOD"),
        sa.Column("data_quality_score", sa.Integer(), nullable=False, server_default="100"),
        sa.UniqueConstraint("factory_id", "date", name="uq_daily_energy_summary"),
    )

    op.create_table(
        "data_quality_log",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("freshness", sa.Float(), nullable=False),
        sa.Column("validity", sa.Float(), nullable=False),
        sa.Column("device_coverage", sa.Float(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("data_quality_log")
    op.drop_table("daily_energy_summary")
    op.drop_table("telemetry_hourly")
    op.drop_table("telemetry_5m")
    op.drop_table("metric_catalog")
    op.drop_table("raw_telemetry")
