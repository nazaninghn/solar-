import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

# 28.10: a lightweight in-process counter store, not a Prometheus/
# Grafana stack — same call as skipping Redis (Step 25/27): this
# project's scale doesn't justify standing up a separate metrics/
# timeseries service yet, and single-instance in-memory counters cover
# everything the DoD checklist actually asks for (request counts,
# error rate, average latency, device/job status). Revisit if this
# ever runs as more than one process, since these counters don't share
# state across instances.

# 77.6: average alone hides tail latency — a bounded reservoir of the
# most recent durations is enough to compute real P50/P90/P95/P99
# without storing every request ever made. 2000 samples is generous
# for a single-instance deployment at this project's traffic scale.
_DURATION_SAMPLE_SIZE = 2000


@dataclass
class _RequestMetrics:
    total: int = 0
    errors_5xx: int = 0
    total_duration_ms: float = 0.0
    bucket_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    recent_durations_ms: deque = field(
        default_factory=lambda: deque(maxlen=_DURATION_SAMPLE_SIZE)
    )


_request_metrics = _RequestMetrics()
_started_at = time.monotonic()


def record_request(status_code: int, duration_ms: float, bucket: str) -> None:
    _request_metrics.total += 1

    if status_code >= 500:
        _request_metrics.errors_5xx += 1

    _request_metrics.total_duration_ms += duration_ms
    _request_metrics.bucket_counts[bucket] += 1
    _request_metrics.recent_durations_ms.append(duration_ms)


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0

    index = min(len(sorted_values) - 1, int(len(sorted_values) * p))
    return sorted_values[index]


def get_request_metrics_snapshot() -> dict:
    total = _request_metrics.total
    average_duration_ms = (_request_metrics.total_duration_ms / total) if total else 0.0
    error_rate_percent = (_request_metrics.errors_5xx / total * 100) if total else 0.0

    sorted_durations = sorted(_request_metrics.recent_durations_ms)

    return {
        "total_requests": total,
        "total_errors_5xx": _request_metrics.errors_5xx,
        "error_rate_percent": round(error_rate_percent, 2),
        "average_duration_ms": round(average_duration_ms, 1),
        "p50_duration_ms": round(_percentile(sorted_durations, 0.50), 1),
        "p90_duration_ms": round(_percentile(sorted_durations, 0.90), 1),
        "p95_duration_ms": round(_percentile(sorted_durations, 0.95), 1),
        "p99_duration_ms": round(_percentile(sorted_durations, 0.99), 1),
        "bucket_counts": dict(_request_metrics.bucket_counts),
        "uptime_seconds": round(time.monotonic() - _started_at, 1),
    }


# 78: per-organization usage, for APIUsageMetric (app/modules/admin/
# models.py, Step 46) — that table existed with no writer, same shape
# as SystemMetricSnapshot before Step 77. Keyed by (organization_id,
# endpoint, method) with endpoint as the ROUTE TEMPLATE
# ("/api/v1/factories/{factory_id}/devices"), not the raw path with
# real IDs substituted in — using the raw path would make this an
# unbounded-cardinality key set (77.72's cardinality-control concern),
# growing one bucket per distinct factory/device/etc ever requested
# instead of one per actual endpoint.
@dataclass
class _OrgEndpointStats:
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0


_org_endpoint_metrics: dict[tuple[int, str, str], _OrgEndpointStats] = defaultdict(
    _OrgEndpointStats
)


def record_org_request(
    organization_id: int | None, endpoint: str, method: str, status_code: int, duration_ms: float
) -> None:
    if organization_id is None:
        return

    stats = _org_endpoint_metrics[(organization_id, endpoint, method)]
    stats.request_count += 1
    if status_code >= 500:
        stats.error_count += 1
    stats.total_duration_ms += duration_ms


def flush_and_reset_org_metrics() -> dict[tuple[int, str, str], _OrgEndpointStats]:
    """Called by the periodic flush job (app/jobs/finops_jobs.py) to get
    everything accumulated since the last flush and clear the buckets —
    the DB row this becomes owns the period_start/period_end, the
    in-memory dict doesn't need to remember old periods too."""
    global _org_endpoint_metrics
    snapshot = _org_endpoint_metrics
    _org_endpoint_metrics = defaultdict(_OrgEndpointStats)
    return snapshot
