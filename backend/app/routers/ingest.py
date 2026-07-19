"""
Ingestion Router
Receives API events from the PulseBoard SDK.
Authenticated via API key (not JWT — SDKs use the project's api_key).

Flow:
  1. Validate api_key → find project
  2. Save raw event to MongoDB (fast, no schema constraint)
  3. Publish to Redis pub/sub so the WebSocket layer can push live updates
  4. Kick off background aggregation task
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid
import json

from app.database import get_db, get_mongo_db
from app.models.postgres_models import Project
from app.schemas.events import EventIn, EventResponse
from app.services.aggregator import aggregate_project

router = APIRouter(prefix="/ingest", tags=["ingest"])


async def get_project_by_api_key(x_api_key: str = Header(...), db: AsyncSession = Depends(get_db)) -> Project:
    result = await db.execute(select(Project).where(Project.api_key == x_api_key))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return project


@router.post("/event", response_model=EventResponse)
async def ingest_event(
    event: EventIn,
    background_tasks: BackgroundTasks,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    mongo_db = get_mongo_db()
    event_id = str(uuid.uuid4())
    ts = event.timestamp or datetime.now(timezone.utc)

    # ── 1. Persist raw event to MongoDB ───────────────────────────────────
    doc = {
        "_id": event_id,
        "project_id": project.id,
        "endpoint": event.endpoint,
        "method": event.method.upper(),
        "status_code": event.status_code,
        "latency_ms": event.latency_ms,
        "timestamp": ts,
        "user_agent": event.user_agent,
        "error_message": event.error_message,
    }
    await mongo_db["raw_events"].insert_one(doc)

    # ── 2. Background: re-aggregate this hour for the project ─────────────
    background_tasks.add_task(aggregate_project, project.id, db, mongo_db)

    return EventResponse(status="accepted", event_id=event_id)


@router.post("/batch", response_model=dict)
async def ingest_batch(
    events: list[EventIn],
    background_tasks: BackgroundTasks,
    project: Project = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Accept up to 100 events at once — the SDK batches to reduce HTTP overhead."""
    if len(events) > 100:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 100 events")

    mongo_db = get_mongo_db()
    docs = []
    for event in events:
        ts = event.timestamp or datetime.now(timezone.utc)
        docs.append({
            "_id": str(uuid.uuid4()),
            "project_id": project.id,
            "endpoint": event.endpoint,
            "method": event.method.upper(),
            "status_code": event.status_code,
            "latency_ms": event.latency_ms,
            "timestamp": ts,
            "user_agent": event.user_agent,
            "error_message": event.error_message,
        })

    if docs:
        await mongo_db["raw_events"].insert_many(docs)

    background_tasks.add_task(aggregate_project, project.id, db, mongo_db)
    return {"status": "accepted", "count": len(docs)}
