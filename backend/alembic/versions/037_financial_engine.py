"""STEP 37: Financial Engine — Prices, Tariffs, Ledgers, Summaries, Reports

Revision ID: 037_financial_engine
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "037_financial_engine"
down_revision = "036_optimization_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "energy_prices_v2",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("market", sa.String(50), nullable=False, server_default="SPOT"),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("unit", sa.String(20), nullable=False, server_default="kWh"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(30), nullable=False, server_default="TIME_OF_USE"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("unit", sa.String(20), nullable=False, server_default="kWh"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("rules_json", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "energy_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("destination", sa.String(30), nullable=False),
        sa.Column("energy_kwh", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(10), nullable=False, server_default="kWh"),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "financial_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("energy_kwh", sa.Float(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "daily_financial_summary",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.String(10), nullable=False, index=True),
        sa.Column("grid_import_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("export_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("solar_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_energy_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("baseline_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_savings", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_energy_benefit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("calculation_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("tariff_version", sa.String(20), nullable=True),
        sa.Column("price_version", sa.String(20), nullable=True),
        sa.Column("data_quality", sa.String(20), nullable=False, server_default="GOOD"),
        sa.UniqueConstraint("factory_id", "date", "calculation_version", name="uq_daily_financial"),
    )

    op.create_table(
        "monthly_financial_summary",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("month", sa.String(7), nullable=False, index=True),
        sa.Column("grid_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("export_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("solar_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("savings", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_benefit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("vs_previous_month", sa.Float(), nullable=True),
        sa.Column("vs_baseline", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.UniqueConstraint("factory_id", "month", name="uq_monthly_financial"),
    )

    op.create_table(
        "financial_reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(30), nullable=False, server_default="MONTHLY"),
        sa.Column("period_start", sa.String(10), nullable=False),
        sa.Column("period_end", sa.String(10), nullable=False),
        sa.Column("calculation_version", sa.String(20), nullable=False),
        sa.Column("tariff_version", sa.String(20), nullable=True),
        sa.Column("price_version", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="GENERATED"),
        sa.Column("snapshot_json", sa.Text(), nullable=True),
        sa.Column("file_reference", sa.String(255), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("financial_reports")
    op.drop_table("monthly_financial_summary")
    op.drop_table("daily_financial_summary")
    op.drop_table("financial_ledger")
    op.drop_table("energy_ledger")
    op.drop_table("tariffs")
    op.drop_table("energy_prices_v2")
