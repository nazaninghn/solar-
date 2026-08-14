"""
STEP 51.37: Circuit Breaker implementation.

Protects the system from repeatedly calling failing external services.
States: CLOSED → OPEN → HALF_OPEN → CLOSED
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.performance.models import CircuitBreakerState

logger = logging.getLogger(__name__)


def get_circuit_state(db: Session, service_name: str) -> CircuitBreakerState:
    """Get or create circuit breaker state for a service."""
    state = db.query(CircuitBreakerState).filter(
        CircuitBreakerState.service_name == service_name
    ).first()
    if not state:
        state = CircuitBreakerState(
            service_name=service_name,
            state="CLOSED",
            created_at=datetime.now(timezone.utc),
        )
        # Note: not committing here, caller manages transaction
    return state


def is_circuit_open(db: Session, service_name: str) -> bool:
    """Check if circuit is open (calls should be blocked)."""
    state = get_circuit_state(db, service_name)

    if state.state == "CLOSED":
        return False

    if state.state == "OPEN":
        # Check if recovery timeout has passed → transition to HALF_OPEN
        if state.opened_at:
            recovery_time = state.opened_at + timedelta(seconds=state.recovery_timeout_seconds)
            if datetime.now(timezone.utc) > recovery_time:
                state.state = "HALF_OPEN"
                state.half_open_at = datetime.now(timezone.utc)
                state.updated_at = datetime.now(timezone.utc)
                db.commit()
                return False  # Allow one test request
        return True

    # HALF_OPEN: allow requests (testing recovery)
    return False


def record_success(db: Session, service_name: str) -> None:
    """Record successful call — close circuit if half-open."""
    state = get_circuit_state(db, service_name)
    state.success_count += 1
    state.last_success_at = datetime.now(timezone.utc)

    if state.state == "HALF_OPEN":
        state.state = "CLOSED"
        state.failure_count = 0
        logger.info(f"Circuit CLOSED for {service_name} (recovered)")

    state.updated_at = datetime.now(timezone.utc)
    db.commit()


def record_failure(db: Session, service_name: str) -> None:
    """Record failed call — open circuit if threshold reached."""
    state = get_circuit_state(db, service_name)
    state.failure_count += 1
    state.last_failure_at = datetime.now(timezone.utc)

    if state.state == "HALF_OPEN":
        # Failed during test → back to OPEN
        state.state = "OPEN"
        state.opened_at = datetime.now(timezone.utc)
        logger.warning(f"Circuit re-OPENED for {service_name} (half-open test failed)")

    elif state.state == "CLOSED" and state.failure_count >= state.failure_threshold:
        state.state = "OPEN"
        state.opened_at = datetime.now(timezone.utc)
        logger.warning(f"Circuit OPENED for {service_name} after {state.failure_count} failures")

    state.updated_at = datetime.now(timezone.utc)
    db.commit()
