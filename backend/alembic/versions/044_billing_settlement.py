"""STEP 44: Billing & Settlement — Plans, Subscriptions, Invoices, Payments, Settlements, Ledger

Revision ID: 044_billing_settlement
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "044_billing_settlement"
down_revision = "043_events_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("plans",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("monthly_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("annual_price", sa.Float(), nullable=True),
        sa.Column("max_factories", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_devices", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("features_json", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("entitlements",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("feature_key", sa.String(100), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_table("subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="TRIALING"),
        sa.Column("billing_cycle", sa.String(10), nullable=False, server_default="MONTHLY"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("usage_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("invoices",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("invoice_number", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "period_start", "period_end", name="uq_invoice_period"),
    )
    op.create_table("invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("metric", sa.String(50), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_table("payments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=True),
        sa.Column("provider", sa.String(30), nullable=False, server_default="MANUAL"),
        sa.Column("provider_reference", sa.String(255), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("settlements",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("import_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("export_revenue", sa.Float(), nullable=False, server_default="0"),
        sa.Column("solar_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("battery_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_energy_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("settlement_adjustments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("settlement_id", sa.Integer(), sa.ForeignKey("settlements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("billing_financial_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("factory_id", sa.Integer(), sa.ForeignKey("factories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("debit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("credit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("billing_financial_ledger")
    op.drop_table("settlement_adjustments")
    op.drop_table("settlements")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("usage_records")
    op.drop_table("subscriptions")
    op.drop_table("entitlements")
    op.drop_table("plans")
