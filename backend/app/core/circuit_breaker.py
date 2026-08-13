import logging
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

logger = logging.getLogger("app.circuit_breaker")

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    """
    28.23: stops hammering a failing external dependency instead of
    retrying it every single call. Distinct from app/jobs/retry.py's
    with_retry — that retries WITHIN one call (a job trying the same
    request up to 3 times); this remembers failures ACROSS calls, so
    once a provider is clearly down, subsequent unrelated requests fail
    immediately instead of each burning their own multi-attempt retry
    budget against a dependency already known to be broken.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_timeout_seconds:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN — refusing to call; "
                f"retry after the {self.recovery_timeout_seconds}s recovery window"
            )

        try:
            result = await func()
        except Exception:
            self._on_failure()
            raise
        else:
            self._on_success(current_state)
            return result

    def _on_failure(self) -> None:
        self._consecutive_failures += 1

        if self._consecutive_failures >= self.failure_threshold and self._state != CircuitState.OPEN:
            logger.warning(
                "circuit breaker '%s' OPENED after %d consecutive failures",
                self.name,
                self._consecutive_failures,
                extra={
                    "circuit_breaker": self.name,
                    "consecutive_failures": self._consecutive_failures,
                },
            )

        if self._consecutive_failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = time.monotonic()

    def _on_success(self, observed_state: CircuitState) -> None:
        if observed_state == CircuitState.HALF_OPEN:
            logger.info(
                "circuit breaker '%s' CLOSED (recovered)",
                self.name,
                extra={"circuit_breaker": self.name},
            )

        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = None
