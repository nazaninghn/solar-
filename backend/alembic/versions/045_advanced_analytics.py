"""STEP 45: Advanced Analytics — KPIs, Aggregations, Forecasts, Anomalies, Device Perf, Impact

Revision ID: 045_advanced_analytics
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "045_advanced_analytics"
down_revision = "044_billing_settlement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("energy_kpis",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("solar_generation_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consumption_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_export_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_charge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_discharge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("self_consumption_rate", sa.Float(), nullable=True),
        sa.Column("solar_coverage_rate", sa.Float(), nullable=True),
        sa.Column("grid_dependency_rate", sa.Float(), nullable=True),
        sa.Column("renewable_share", sa.Float(), nullable=True),
        sa.Column("peak_demand_kw", sa.Float(), nullable=True),
        sa.Column("load_factor", sa.Float(), nullable=True),
        sa.Column("calculation_version", sa.String(20), nullable=False, server_default="kpi-v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("factory_id", "period_start", "period_end", name="uq_energy_kpi"),
    )
    op.create_table("hourly_energy_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("hour", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("solar_generation_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consumption_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_export_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_charge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_discharge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peak_power_kw", sa.Float(), nullable=True),
        sa.Column("average_power_kw", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("factory_id", "hour", name="uq_hourly_energy"),
    )
    op.create_table("daily_energy_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False, index=True),
        sa.Column("solar_generation_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consumption_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_import_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("grid_export_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_charge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_discharge_kwh", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peak_demand_kw", sa.Float(), nullable=True),
        sa.Column("solar_coverage_rate", sa.Float(), nullable=True),
        sa.Column("self_consumption_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("factory_id", "date", name="uq_daily_energy_metric"),
    )
    op.create_table("forecast_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("forecast_type", sa.String(50), nullable=False, index=True),
        sa.Column("target_timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(20), nullable=False, server_default="kWh"),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("anomalies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("device_id", sa.Integer(), nullable=True, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=True),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("deviation", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DETECTED"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_table("device_performance",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("availability", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("efficiency", sa.Float(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("production_kwh", sa.Float(), nullable=True),
        sa.Column("performance_ratio", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("device_id", "period_start", name="uq_device_perf"),
    )
    op.create_table("recommendation_impacts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("recommendation_id", sa.Integer(), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("baseline_cost", sa.Float(), nullable=False),
        sa.Column("actual_cost", sa.Float(), nullable=False),
        sa.Column("estimated_saving", sa.Float(), nullable=False),
        sa.Column("realized_saving", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("measurement_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("measurement_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recommendation_impacts")
    op.drop_table("device_performance")
    op.drop_table("anomalies")
    op.drop_table("forecast_records")
    op.drop_table("daily_energy_metrics")
    op.drop_table("hourly_energy_metrics")
    op.drop_table("energy_kpis")
