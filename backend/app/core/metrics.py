import time
from collections import defaultdict
from dataclasses import dataclass, field

# 28.10: a lightweight in-process counter store, not a Prometheus/
# Grafana stack — same call as skipping Redis (Step 25/27): this
# project's scale doesn't justify standing up a separate metrics/
# timeseries service yet, and single-instance in-memory counters cover
# everything the DoD checklist actually asks for (request counts,
# error rate, average latency, device/job status). Revisit if this
# ever runs as more than one process, since these counters don't share
# state across instances.


@dataclass
class _RequestMetrics:
    total: int = 0
    errors_5xx: int = 0
    total_duration_ms: float = 0.0
    bucket_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))


_request_metrics = _RequestMetrics()
_started_at = time.monotonic()


def record_request(status_code: int, duration_ms: float, bucket: str) -> None:
    _request_metrics.total += 1

    if status_code >= 500:
        _request_metrics.errors_5xx += 1

    _request_metrics.total_duration_ms += duration_ms
    _request_metrics.bucket_counts[bucket] += 1


def get_request_metrics_snapshot() -> dict:
    total = _request_metrics.total
    average_duration_ms = (_request_metrics.total_duration_ms / total) if total else 0.0
    error_rate_percent = (_request_metrics.errors_5xx / total * 100) if total else 0.0

    return {
        "total_requests": total,
        "total_errors_5xx": _request_metrics.errors_5xx,
        "error_rate_percent": round(error_rate_percent, 2),
        "average_duration_ms": round(average_duration_ms, 1),
        "bucket_counts": dict(_request_metrics.bucket_counts),
        "uptime_seconds": round(time.monotonic() - _started_at, 1),
    }
