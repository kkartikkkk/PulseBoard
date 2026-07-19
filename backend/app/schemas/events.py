from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Ingestion ──────────────────────────────────────────────────────────────
class EventIn(BaseModel):
    """Payload the SDK sends for each API request."""
    endpoint: str = Field(..., example="/api/users")
    method: str = Field(..., example="GET")
    status_code: int = Field(..., example=200)
    latency_ms: float = Field(..., example=42.5)
    timestamp: Optional[datetime] = None  # defaults to now() server-side
    user_agent: Optional[str] = None
    error_message: Optional[str] = None


class EventResponse(BaseModel):
    status: str = "accepted"
    event_id: str


# ── Analytics ─────────────────────────────────────────────────────────────
class MetricPoint(BaseModel):
    hour_bucket: datetime
    endpoint: str
    method: str
    total_requests: int
    error_count: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float


class AnomalyAlertOut(BaseModel):
    id: int
    endpoint: str
    alert_type: str
    message: str
    severity: str
    triggered_at: datetime
    resolved: bool

    class Config:
        from_attributes = True


# ── Auth ──────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True
