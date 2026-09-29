"""Day-ahead market — PTF prices, fundamentals, forecasts, sell offers

Revision ID: 054_market_ptf
Revises: 053_failure_prediction
Create Date: 2026-09-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "054_market_ptf"
down_revision = "053_failure_prediction"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_prices",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, unique=True, index=True),
        sa.Column("ptf_try_mwh", sa.Float(), nullable=True),
        sa.Column("ptf_usd_mwh", sa.Float(), nullable=True),
        sa.Column("ptf_eur_mwh", sa.Float(), nullable=True),
        sa.Column("smf_try_mwh", sa.Float(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="EPIAS"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "market_fundamentals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, unique=True, index=True),
        sa.Column("load_forecast_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_total_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_wind_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_solar_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_hydro_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_river_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_natural_gas_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_lignite_mwh", sa.Float(), nullable=True),
        sa.Column("dpp_imported_coal_mwh", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ptf_forecasts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("delivery_date", sa.Date(), nullable=False, index=True),
        sa.Column("p10_try_mwh", sa.Float(), nullable=False),
        sa.Column("p50_try_mwh", sa.Float(), nullable=False),
        sa.Column("p90_try_mwh", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("timestamp", "model_version", name="uq_ptf_forecast_hour_model"),
    )
    op.create_table(
        "sell_offers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("delivery_date", sa.Date(), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("quantity_mwh", sa.Float(), nullable=False),
        sa.Column("price_try_mwh", sa.Float(), nullable=True),
        sa.Column("expected_ptf_try_mwh", sa.Float(), nullable=True),
        sa.Column("expected_revenue_try", sa.Float(), nullable=True),
        sa.Column("revenue_p10_try", sa.Float(), nullable=True),
        sa.Column("revenue_p90_try", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("factory_id", "timestamp", "tier", name="uq_sell_offer_factory_hour_tier"),
    )


def downgrade() -> None:
    op.drop_table("sell_offers")
    op.drop_table("ptf_forecasts")
    op.drop_table("market_fundamentals")
    op.drop_table("market_prices")
