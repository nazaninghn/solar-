"""
STEP 79.29-79.30: Security Event Correlation.

SecurityEvent rows (app/modules/security/audit_service.py, Step 53)
have always been logged individually — nothing groups related events
into a single "this looks like an actual incident" signal. This reuses
MonitoringIncident (Step 49) as the correlated output rather than
inventing a new table: a correlated security pattern IS a production
incident, and reusing it gets acknowledge/resolve/timeline/postmortem
for free instead of building a parallel workflow around a new model.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.monitoring.models import MonitoringIncident
from app.modules.security.models import SecurityEvent

CORRELATION_WINDOW_MINUTES = 15
BRUTE_FORCE_THRESHOLD = 3

# 79.30's example pattern list, kept intentionally small — each one is
# either a volume threshold (many of the same low-severity event is
# itself a signal) or a combination that individually-logged events
# never surface (a role change AND a permission denial for the same
# user close together is more suspicious than either alone).
_INHERENTLY_SUSPICIOUS_TYPES = ("IDOR_ATTEMPT", "INJECTION_ATTEMPT")


def _dedup_key(pattern: str, subject: str) -> str:
    return f"{pattern}:{subject}"


def _incident_already_open(db: Session, dedup_key: str) -> bool:
    return (
        db.scalar(
            select(MonitoringIncident.id).where(
                MonitoringIncident.service == "security",
                MonitoringIncident.title.like(f"%{dedup_key}%"),
                MonitoringIncident.status.in_(["OPEN", "ACKNOWLEDGED", "INVESTIGATING"]),
            )
        )
        is not None
    )


def _open_incident(db: Session, dedup_key: str, pattern: str, severity: str, detail: str) -> bool:
    if _incident_already_open(db, dedup_key):
        return False

    now = datetime.now(timezone.utc)
    db.add(
        MonitoringIncident(
            title=f"Correlated security activity: {pattern} ({dedup_key})",
            severity=severity,
            status="OPEN",
            service="security",
            started_at=now,
            root_cause=detail,
            created_at=now,
        )
    )
    db.commit()
    return True


def detect_correlated_security_activity(db: Session) -> int:
    """Returns the number of new correlated incidents opened."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=CORRELATION_WINDOW_MINUTES)

    recent_events = db.scalars(
        select(SecurityEvent).where(SecurityEvent.created_at >= window_start)
    ).all()

    by_ip: dict[str, list[SecurityEvent]] = defaultdict(list)
    by_user: dict[int, list[SecurityEvent]] = defaultdict(list)
    for event in recent_events:
        if event.ip_address:
            by_ip[event.ip_address].append(event)
        if event.user_id:
            by_user[event.user_id].append(event)

    created = 0

    # Pattern: repeated failed logins from the same IP in the window.
    for ip, events in by_ip.items():
        failed = [e for e in events if e.event_type == "LOGIN_FAILED"]
        if len(failed) >= BRUTE_FORCE_THRESHOLD:
            key = _dedup_key("BRUTE_FORCE_LOGIN", ip)
            if _open_incident(
                db, key, "BRUTE_FORCE_LOGIN", "MEDIUM",
                f"{len(failed)} failed logins from {ip} within {CORRELATION_WINDOW_MINUTES} minutes",
            ):
                created += 1

    # Pattern: privilege change + a subsequent permission denial for the
    # same user — could be legitimate (role changed, old cached token
    # briefly rejected) but worth a human glance either way.
    for user_id, events in by_user.items():
        event_types = {e.event_type for e in events}
        if "ROLE_CHANGED" in event_types and "PERMISSION_DENIED" in event_types:
            key = _dedup_key("PRIVILEGE_ESCALATION_PATTERN", str(user_id))
            if _open_incident(
                db, key, "PRIVILEGE_ESCALATION_PATTERN", "HIGH",
                f"user_id={user_id}: role change and permission denial within "
                f"{CORRELATION_WINDOW_MINUTES} minutes",
            ):
                created += 1

    # Inherently high-signal event types — one occurrence is enough,
    # no volume threshold needed.
    for event in recent_events:
        if event.event_type in _INHERENTLY_SUSPICIOUS_TYPES:
            subject = str(event.user_id or event.ip_address or event.id)
            key = _dedup_key(event.event_type, subject)
            if _open_incident(
                db, key, event.event_type, "HIGH",
                event.description or f"{event.event_type} detected",
            ):
                created += 1

    return created
