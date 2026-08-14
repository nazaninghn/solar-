"""
STEP 77.2-77.7: periodic system_metric_snapshots writer.

SystemMetricSnapshot (Step 41) has existed since the observability
module was first built, but nothing ever wrote to it — it's an empty
table. This is the missing writer: a time series over the golden
signals (traffic/errors/latency/saturation) that both SLO computation
(app.modules.observability.slo) and anomaly detection
(app.modules.observability.anomaly_detection) need real history for.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.external_api_metrics import get_external_api_snapshot
from app.core.metrics import get_request_metrics_snapshot
from app.modules.observability.models import SystemMetricSnapshot
from app.modules.system.service import get_device_status_counts


def record_system_metric_snapshots(db: Session) -> int:
    now = datetime.now(timezone.utc)
    request_metrics = get_request_metrics_snapshot()
    device_counts = get_device_status_counts(db)

    rows = [
        SystemMetricSnapshot(
            timestamp=now, metric="api.error_rate_percent",
            value=request_metrics["error_rate_percent"],
        ),
        SystemMetricSnapshot(
            timestamp=now, metric="api.average_duration_ms",
            value=request_metrics["average_duration_ms"],
        ),
        SystemMetricSnapshot(
            timestamp=now, metric="api.p95_duration_ms",
            value=request_metrics["p95_duration_ms"],
        ),
        SystemMetricSnapshot(
            timestamp=now, metric="api.total_requests",
            value=float(request_metrics["total_requests"]),
        ),
        SystemMetricSnapshot(
            timestamp=now, metric="devices.online_count",
            value=float(device_counts["online"]),
        ),
        SystemMetricSnapshot(
            timestamp=now, metric="devices.offline_count",
            value=float(device_counts["offline"]),
        ),
    ]

    for service_name, snapshot in get_external_api_snapshot().items():
        rows.append(
            SystemMetricSnapshot(
                timestamp=now,
                metric="external_api.success_rate_percent",
                value=snapshot["success_rate_percent"],
                tags_json=json.dumps({"service": service_name}),
            )
        )

    db.add_all(rows)
    db.commit()

    return len(rows)
