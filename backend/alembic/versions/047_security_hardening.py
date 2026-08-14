"""STEP 47: Security — Events, Lockouts, Backups, DR Plans

Revision ID: 047_security_hardening
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "047_security_hardening"
down_revision = "046_admin_panel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("security_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("account_lockouts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_reason", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("backup_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("backup_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_location", sa.String(500), nullable=True),
        sa.Column("encrypted", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_table("disaster_recovery_plans",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("scenario", sa.String(100), nullable=False),
        sa.Column("rpo_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("rto_minutes", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("runbook", sa.Text(), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("test_result", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("disaster_recovery_plans")
    op.drop_table("backup_records")
    op.drop_table("account_lockouts")
    op.drop_table("security_events")
