from collections import defaultdict
from dataclasses import dataclass


@dataclass
class _ApiStats:
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    total_latency_ms: float = 0.0


_stats: dict[str, _ApiStats] = defaultdict(_ApiStats)


def record_external_call(
    service: str, success: bool, latency_ms: float, timed_out: bool = False
) -> None:
    """28.21: per-external-API counters — Weather is the only real
    external dependency today (pricing/email/SMS are still stubs from
    earlier steps), but this is written to key off `service` so adding
    a second provider later doesn't need new plumbing, just a new call
    site."""
    stats = _stats[service]
    stats.request_count += 1
    stats.total_latency_ms += latency_ms

    if success:
        stats.success_count += 1
    else:
        stats.failure_count += 1

    if timed_out:
        stats.timeout_count += 1


def get_external_api_snapshot() -> dict[str, dict]:
    result = {}

    for service, stats in _stats.items():
        success_rate = (
            (stats.success_count / stats.request_count * 100)
            if stats.request_count
            else 100.0
        )
        average_latency_ms = (
            (stats.total_latency_ms / stats.request_count) if stats.request_count else 0.0
        )

        # 28.22: rough bands — healthy/degraded/unhealthy, not a tuned SLA.
        if success_rate >= 99:
            api_status = "healthy"
        elif success_rate >= 90:
            api_status = "degraded"
        else:
            api_status = "unhealthy"

        result[service] = {
            "request_count": stats.request_count,
            "success_count": stats.success_count,
            "failure_count": stats.failure_count,
            "timeout_count": stats.timeout_count,
            "success_rate_percent": round(success_rate, 2),
            "average_latency_ms": round(average_latency_ms, 1),
            "status": api_status,
        }

    return result
