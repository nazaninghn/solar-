"""STEP 35: Forecasting Engine — Forecasts, Points, Accuracy, Model Registry

Revision ID: 035_forecasting_engine
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "035_forecasting_engine"
down_revision = "034_data_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False, index=True),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution", sa.String(10), nullable=False, server_default="1h"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("status", sa.String(20), nullable=False, server_default="READY"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "forecast_points",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("forecast_id", sa.Integer(), sa.ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("lower_bound", sa.Float(), nullable=True),
        sa.Column("upper_bound", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("quality", sa.String(20), nullable=False, server_default="GOOD"),
    )

    op.create_table(
        "forecast_accuracy",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("forecast_id", sa.Integer(), sa.ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=False),
        sa.Column("error", sa.Float(), nullable=False),
        sa.Column("absolute_error", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("forecast_id", "timestamp", name="uq_forecast_accuracy"),
    )

    op.create_table(
        "forecast_model_registry",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PRODUCTION"),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("rmse", sa.Float(), nullable=True),
        sa.Column("mape", sa.Float(), nullable=True),
        sa.Column("features_json", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("forecast_model_registry")
    op.drop_table("forecast_accuracy")
    op.drop_table("forecast_points")
    op.drop_table("forecasts")
