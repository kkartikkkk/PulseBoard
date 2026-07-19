"""
Aggregator Service
Reads raw events from MongoDB and computes hourly aggregates,
then upserts them into PostgreSQL HourlyMetric rows.
Also triggers anomaly detection and persists alerts.
"""

import statistics
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.postgres_models import HourlyMetric, AnomalyAlert
from app.services.anomaly import run_all_checks


def floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


async def aggregate_project(project_id: str, db: AsyncSession, mongo_db: AsyncIOMotorDatabase):
    """
    Pull the last hour of raw events from MongoDB for this project,
    compute per-endpoint stats, upsert into PostgreSQL, then run anomaly checks.
    """
    now = datetime.now(timezone.utc)
    current_hour = floor_to_hour(now)

    collection = mongo_db["raw_events"]

    # Pull events for this hour
    cursor = collection.find({
        "project_id": project_id,
        "timestamp": {"$gte": current_hour}
    })
    events = await cursor.to_list(length=10000)

    if not events:
        return

    # Group by endpoint+method
    grouped: dict = {}
    for evt in events:
        key = (evt["endpoint"], evt["method"])
        grouped.setdefault(key, []).append(evt)

    for (endpoint, method), evts in grouped.items():
        latencies = [e["latency_ms"] for e in evts]
        errors = [e for e in evts if e["status_code"] >= 400]

        avg_lat = statistics.mean(latencies)
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        p95 = sorted_lat[int(n * 0.95) - 1] if n >= 20 else sorted_lat[-1]
        p99 = sorted_lat[int(n * 0.99) - 1] if n >= 100 else sorted_lat[-1]

        # Upsert into PostgreSQL
        stmt = select(HourlyMetric).where(
            HourlyMetric.project_id == project_id,
            HourlyMetric.endpoint == endpoint,
            HourlyMetric.method == method,
            HourlyMetric.hour_bucket == current_hour,
        )
        result = await db.execute(stmt)
        metric = result.scalar_one_or_none()

        if metric:
            metric.total_requests = n
            metric.error_count = len(errors)
            metric.avg_latency_ms = round(avg_lat, 2)
            metric.p95_latency_ms = round(p95, 2)
            metric.p99_latency_ms = round(p99, 2)
        else:
            metric = HourlyMetric(
                project_id=project_id,
                endpoint=endpoint,
                method=method,
                hour_bucket=current_hour,
                total_requests=n,
                error_count=len(errors),
                avg_latency_ms=round(avg_lat, 2),
                p95_latency_ms=round(p95, 2),
                p99_latency_ms=round(p99, 2),
            )
            db.add(metric)

        await db.commit()

    # ── Anomaly detection against last 24 hours of history ────────────────
    await _run_anomaly_checks(project_id, endpoint, method, db)


async def _run_anomaly_checks(project_id: str, endpoint: str, method: str, db: AsyncSession):
    """Pull last 24 hourly rows and run statistical checks."""
    stmt = (
        select(HourlyMetric)
        .where(
            HourlyMetric.project_id == project_id,
            HourlyMetric.endpoint == endpoint,
            HourlyMetric.method == method,
        )
        .order_by(HourlyMetric.hour_bucket.desc())
        .limit(25)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if len(rows) < 6:
        return  # not enough history

    current = rows[0]
    history = rows[1:]

    current_error_rate = current.error_count / max(current.total_requests, 1)

    alerts = run_all_checks(
        endpoint=endpoint,
        current_latency=current.avg_latency_ms,
        current_error_rate=current_error_rate,
        current_requests=current.total_requests,
        historical_latencies=[r.avg_latency_ms for r in history],
        historical_error_rates=[r.error_count / max(r.total_requests, 1) for r in history],
        historical_requests=[r.total_requests for r in history],
    )

    for alert in alerts:
        db.add(AnomalyAlert(
            project_id=project_id,
            endpoint=alert["endpoint"],
            alert_type=alert["alert_type"],
            message=alert["message"],
            severity=alert["severity"],
        ))

    if alerts:
        await db.commit()
