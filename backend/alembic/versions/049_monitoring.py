"""STEP 49: Monitoring — Incidents, Events, Alert Rules, Deployments, Postmortems

Revision ID: 049_monitoring
Create Date: 2026-08-14
"""

from alembic import op
import sqlalchemy as sa

revision = "049_monitoring"
down_revision = "047_security_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("monitoring_incidents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="WARNING"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("service", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("incident_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("monitoring_incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("monitoring_alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("metric", sa.String(100), nullable=False),
        sa.Column("operator", sa.String(10), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="WARNING"),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("deployment_records",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("environment", sa.String(20), nullable=False, server_default="production"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DEPLOYED"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deployed_by", sa.String(100), nullable=True),
        sa.Column("rollback_of", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table("incident_postmortems",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("monitoring_incidents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("customer_impact", sa.Text(), nullable=True),
        sa.Column("technical_impact", sa.Text(), nullable=True),
        sa.Column("timeline", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("preventive_actions", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("incident_postmortems")
    op.drop_table("deployment_records")
    op.drop_table("monitoring_alert_rules")
    op.drop_table("incident_events")
    op.drop_table("monitoring_incidents")
