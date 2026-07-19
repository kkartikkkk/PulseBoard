from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="owner", cascade="all, delete")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False, default=generate_uuid)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="projects")
    hourly_metrics = relationship("HourlyMetric", back_populates="project", cascade="all, delete")


class HourlyMetric(Base):
    """Aggregated metrics per endpoint per hour — stored in PostgreSQL for fast queries."""
    __tablename__ = "hourly_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    hour_bucket = Column(DateTime(timezone=True), nullable=False, index=True)

    total_requests = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    p99_latency_ms = Column(Float, default=0.0)

    project = relationship("Project", back_populates="hourly_metrics")


class AnomalyAlert(Base):
    """Persisted anomaly alerts so users can review history."""
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # "latency_spike" | "error_rate_spike" | "traffic_spike"
    message = Column(String, nullable=False)
    severity = Column(String, default="warning")  # "warning" | "critical"
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved = Column(Integer, default=0)  # 0=open, 1=resolved
