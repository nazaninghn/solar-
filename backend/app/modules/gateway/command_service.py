"""
STEP 33.11-33.14: Command Service.

Bridges Control layer (STEP 32) with Device Gateway (STEP 33).
Handles command delivery, ACK processing, verification, and DLQ.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.control.models import CMD_FAILED, CMD_PENDING, CMD_SENT, CMD_SUCCESS, CommandQueue
from app.modules.gateway.adapters.base import DeviceAdapter

logger = logging.getLogger(__name__)

# Configuration
MAX_RETRIES = 3
COMMAND_TIMEOUT_SECONDS = 30


async def process_pending_commands(
    db: Session,
    adapter: DeviceAdapter,
) -> list[dict]:
    """
    33.14: Worker picks up pending commands and sends them via adapter.
    Returns list of results.
    """
    pending = (
        db.query(CommandQueue)
        .filter(CommandQueue.status == CMD_PENDING)
        .order_by(CommandQueue.created_at.asc())
        .limit(10)
        .all()
    )

    results: list[dict] = []

    for command in pending:
        # Max retries check
        if command.attempt_count >= MAX_RETRIES:
            command.status = CMD_FAILED
            command.error = f"Max retries ({MAX_RETRIES}) exceeded"
            db.commit()
            logger.error(
                f"Command {command.id} moved to DLQ after {MAX_RETRIES} retries",
                extra={"command_id": command.id, "action_id": command.action_id},
            )
            results.append({"command_id": command.id, "status": "DLQ"})
            continue

        # Increment attempt
        command.attempt_count += 1
        command.sent_at = datetime.now(timezone.utc)
        command.status = CMD_SENT
        db.commit()

        # Parse payload
        payload = json.loads(command.payload_json) if command.payload_json else {}

        # Send via adapter
        try:
            result = await adapter.send_command(
                device_id=str(command.device_id),
                command_id=command.idempotency_key,
                command_type=command.command_type,
                payload=payload,
            )

            if result.success:
                command.status = CMD_SUCCESS
                command.completed_at = datetime.now(timezone.utc)
                command.error = None
                logger.info(
                    f"Command {command.id} succeeded",
                    extra={"command_id": command.id, "device_id": command.device_id},
                )
            else:
                command.status = CMD_PENDING  # Will retry
                command.error = result.error
                logger.warning(
                    f"Command {command.id} failed (attempt {command.attempt_count}): {result.error}",
                    extra={"command_id": command.id},
                )

        except Exception as e:
            command.status = CMD_PENDING  # Will retry
            command.error = str(e)
            logger.exception(
                f"Command {command.id} exception",
                extra={"command_id": command.id},
            )

        db.commit()
        results.append({
            "command_id": command.id,
            "status": command.status,
            "attempt": command.attempt_count,
        })

    return results


async def verify_command_execution(
    db: Session,
    command: CommandQueue,
    adapter: DeviceAdapter,
    expected_power_kw: float | None = None,
) -> bool:
    """
    33.17: After command success, verify device actually changed state.
    """
    state = await adapter.get_state(str(command.device_id))

    if not state.online:
        logger.warning(f"Verification failed: device {command.device_id} offline")
        return False

    # Verify power matches (with tolerance)
    if expected_power_kw is not None and state.power_kw is not None:
        tolerance = abs(expected_power_kw) * 0.1  # 10% tolerance
        actual = abs(state.power_kw)
        expected = abs(expected_power_kw)
        if abs(actual - expected) > tolerance:
            logger.warning(
                f"Verification failed: expected ~{expected_power_kw}kW, got {state.power_kw}kW",
                extra={"command_id": command.id, "device_id": command.device_id},
            )
            return False

    return True
