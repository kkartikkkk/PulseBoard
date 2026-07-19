"""
Analytics Router
Serves aggregated metrics and anomaly alerts to the frontend.
Also handles the WebSocket connection for real-time live updates.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone, timedelta
from typing import Optional
import asyncio
import json

from app.database import get_db, get_mongo_db
from app.models.postgres_models import HourlyMetric, AnomalyAlert, Project
from app.schemas.events import MetricPoint, AnomalyAlertOut
from app.routers.auth import get_current_user
from app.models.postgres_models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── WebSocket connection manager ──────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # project_id → list of active WebSocket connections
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(project_id, []).append(ws)

    def disconnect(self, project_id: str, ws: WebSocket):
        if project_id in self.active:
            self.active[project_id].discard(ws) if hasattr(self.active[project_id], 'discard') else None
            try:
                self.active[project_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, project_id: str, message: dict):
        dead = []
        for ws in self.active.get(project_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(project_id, ws)


manager = ConnectionManager()


# ── Helper: verify project ownership ─────────────────────────────────────
async def get_owned_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ── Endpoints ─────────────────────────────────────────────────────────────
@router.get("/{project_id}/metrics", response_model=list[MetricPoint])
async def get_metrics(
    project_id: str,
    hours: int = Query(default=24, ge=1, le=168),  # up to 7 days
    endpoint: Optional[str] = Query(default=None),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = (
        select(HourlyMetric)
        .where(
            HourlyMetric.project_id == project_id,
            HourlyMetric.hour_bucket >= since,
        )
        .order_by(HourlyMetric.hour_bucket.desc())
    )
    if endpoint:
        stmt = stmt.where(HourlyMetric.endpoint == endpoint)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        MetricPoint(
            hour_bucket=row.hour_bucket,
            endpoint=row.endpoint,
            method=row.method,
            total_requests=row.total_requests,
            error_count=row.error_count,
            avg_latency_ms=row.avg_latency_ms,
            p95_latency_ms=row.p95_latency_ms,
            p99_latency_ms=row.p99_latency_ms,
            error_rate=round(row.error_count / max(row.total_requests, 1), 4),
        )
        for row in rows
    ]


@router.get("/{project_id}/alerts", response_model=list[AnomalyAlertOut])
async def get_alerts(
    project_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    unresolved_only: bool = Query(default=False),
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(AnomalyAlert)
        .where(AnomalyAlert.project_id == project_id)
        .order_by(desc(AnomalyAlert.triggered_at))
        .limit(limit)
    )
    if unresolved_only:
        stmt = stmt.where(AnomalyAlert.resolved == 0)

    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return [AnomalyAlertOut(
        id=a.id,
        endpoint=a.endpoint,
        alert_type=a.alert_type,
        message=a.message,
        severity=a.severity,
        triggered_at=a.triggered_at,
        resolved=bool(a.resolved),
    ) for a in alerts]


@router.patch("/{project_id}/alerts/{alert_id}/resolve")
async def resolve_alert(
    project_id: str,
    alert_id: int,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnomalyAlert).where(AnomalyAlert.id == alert_id, AnomalyAlert.project_id == project_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = 1
    await db.commit()
    return {"status": "resolved"}


@router.get("/{project_id}/summary")
async def get_summary(
    project_id: str,
    project: Project = Depends(get_owned_project),
    db: AsyncSession = Depends(get_db),
):
    """Quick summary card: total requests today, avg latency, top endpoint, open alerts."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(
        select(HourlyMetric).where(
            HourlyMetric.project_id == project_id,
            HourlyMetric.hour_bucket >= since,
        )
    )
    rows = result.scalars().all()

    total_requests = sum(r.total_requests for r in rows)
    total_errors = sum(r.error_count for r in rows)
    avg_latency = (
        sum(r.avg_latency_ms * r.total_requests for r in rows) / total_requests
        if total_requests > 0 else 0
    )

    # Find busiest endpoint
    endpoint_counts: dict[str, int] = {}
    for r in rows:
        endpoint_counts[r.endpoint] = endpoint_counts.get(r.endpoint, 0) + r.total_requests
    top_endpoint = max(endpoint_counts, key=endpoint_counts.get) if endpoint_counts else None

    # Open alerts
    alerts_result = await db.execute(
        select(AnomalyAlert).where(
            AnomalyAlert.project_id == project_id,
            AnomalyAlert.resolved == 0,
        )
    )
    open_alerts = len(alerts_result.scalars().all())

    return {
        "total_requests_24h": total_requests,
        "total_errors_24h": total_errors,
        "error_rate_24h": round(total_errors / max(total_requests, 1), 4),
        "avg_latency_ms": round(avg_latency, 2),
        "top_endpoint": top_endpoint,
        "open_alerts": open_alerts,
    }


# ── WebSocket: real-time live feed ────────────────────────────────────────
@router.websocket("/{project_id}/live")
async def live_feed(project_id: str, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """
    Clients connect here and receive a metrics snapshot every 5 seconds.
    In production, you'd use Redis pub/sub to push on every event instead of polling.
    This polling approach is simpler and works great for demos.
    """
    await manager.connect(project_id, websocket)
    try:
        while True:
            # Send a summary snapshot every 5 seconds
            since = datetime.now(timezone.utc) - timedelta(minutes=5)
            result = await db.execute(
                select(HourlyMetric).where(
                    HourlyMetric.project_id == project_id,
                    HourlyMetric.hour_bucket >= since,
                )
            )
            rows = result.scalars().all()

            total = sum(r.total_requests for r in rows)
            errors = sum(r.error_count for r in rows)
            avg_lat = (
                sum(r.avg_latency_ms * r.total_requests for r in rows) / total
                if total > 0 else 0
            )

            await websocket.send_json({
                "type": "live_snapshot",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_requests_5m": total,
                "error_count_5m": errors,
                "avg_latency_ms": round(avg_lat, 2),
            })

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
