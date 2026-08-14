"""STEP 36: Optimization Engine — Smart Recommendations, Flexible Loads, History, Snapshots

Revision ID: 036_optimization_engine
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "036_optimization_engine"
down_revision = "035_forecasting_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "smart_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING_APPROVAL"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_savings", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expected_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("savings_lower", sa.Float(), nullable=True),
        sa.Column("savings_upper", sa.Float(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("reason_codes_json", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("rules_version", sa.String(50), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("dedup_key", sa.String(255), nullable=True, index=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_savings", sa.Float(), nullable=True),
        sa.Column("actual_revenue", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "flexible_loads",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("power_kw", sa.Float(), nullable=False),
        sa.Column("energy_kwh", sa.Float(), nullable=False),
        sa.Column("earliest_start", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latest_end", sa.Integer(), nullable=False, server_default="23"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("allowed_days_json", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )

    op.create_table(
        "recommendation_history",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("smart_recommendations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("old_value", sa.String(30), nullable=True),
        sa.Column("new_value", sa.String(30), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "optimization_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("smart_recommendations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("forecast_version", sa.String(50), nullable=True),
        sa.Column("price_version", sa.String(50), nullable=True),
        sa.Column("battery_soc", sa.Float(), nullable=True),
        sa.Column("rules_version", sa.String(50), nullable=True),
        sa.Column("data_quality_score", sa.Integer(), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("optimization_snapshots")
    op.drop_table("recommendation_history")
    op.drop_table("flexible_loads")
    op.drop_table("smart_recommendations")
