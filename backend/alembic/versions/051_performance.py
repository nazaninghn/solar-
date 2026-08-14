"""STEP 51: Performance — Capacity, Budgets, Quotas, Circuit Breakers

Revision ID: 051_performance
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "051_performance"
down_revision = "050_data_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("capacity_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("current_capacity", sa.Float(), nullable=False),
        sa.Column("target_capacity", sa.Float(), nullable=True),
        sa.Column("warning_threshold", sa.Float(), nullable=True),
        sa.Column("critical_threshold", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(20), nullable=False, server_default="count"),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("performance_budgets",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("endpoint", sa.String(200), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("p50_target_ms", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("p95_target_ms", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("p99_target_ms", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("max_error_rate_pct", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("tenant_quotas",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("max_factories", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_devices", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("max_api_requests_per_min", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("max_telemetry_per_min", sa.Integer(), nullable=False, server_default="5000"),
        sa.Column("max_storage_gb", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("max_reports_per_day", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("circuit_breaker_states",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("service_name", sa.String(100), nullable=False, unique=True),
        sa.Column("state", sa.String(20), nullable=False, server_default="CLOSED"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("half_open_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("recovery_timeout_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("circuit_breaker_states")
    op.drop_table("tenant_quotas")
    op.drop_table("performance_budgets")
    op.drop_table("capacity_metrics")
