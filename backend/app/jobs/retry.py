import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

# 25.24-25.25: 3 attempts total, with growing (not fixed) waits between
# them so a struggling external API sees progressively less pressure
# instead of being hammered at a constant rate.
DEFAULT_BACKOFF_SECONDS = (10, 30, 90)


async def with_retry(
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    backoff_seconds: tuple[int, ...] = DEFAULT_BACKOFF_SECONDS,
) -> T:
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as error:
            last_error = error

            if attempt < max_attempts - 1:
                delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                await asyncio.sleep(delay)

    raise last_error
