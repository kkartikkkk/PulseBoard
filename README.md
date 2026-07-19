# PulseBoard — Real-Time API Analytics & Anomaly Detection

> Monitor every API request. Detect anomalies automatically. Ship it yourself.

PulseBoard is a self-hostable alternative to Datadog/New Relic. Drop the SDK into any Python app, and get a live dashboard showing latency, error rates, traffic spikes, and AI-detected anomalies — all in real time.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) — async, high-throughput |
| Raw event store | MongoDB — schema-flexible, high-write volume |
| Aggregated metrics | PostgreSQL — structured queries, fast reads |
| Real-time | WebSockets (FastAPI native) |
| Anomaly detection | Python statistics (Z-score, IQR) |
| Frontend | React + TailwindCSS + Recharts |
| Infrastructure | Docker + Docker Compose |
| Auth | JWT (python-jose + bcrypt) |

---

## Architecture

```
Your App
  └─► PulseBoard SDK (ASGI middleware)
          │
          ▼
  FastAPI /ingest/batch          ← high-throughput event ingestion
          │
          ├─► MongoDB             ← raw events (schema-free, fast writes)
          │
          └─► BackgroundTask
                  │
                  ▼
         Python Aggregator        ← compute hourly stats per endpoint
                  │
                  ├─► PostgreSQL  ← hourly_metrics, alerts (structured)
                  │
                  └─► Anomaly Detector (Z-score)
                              │
                              ▼
                    AnomalyAlert rows in PostgreSQL

FastAPI /analytics/{project_id}
  ├─ GET /summary        ← summary card data
  ├─ GET /metrics        ← time-series metrics
  ├─ GET /alerts         ← anomaly alerts
  └─ WS  /live           ← WebSocket: 5-second live snapshots

React Dashboard
  ├─ SummaryCards        ← requests, latency, error rate, open alerts
  ├─ MetricsChart        ← bar chart (requests/errors) + line chart (latency)
  ├─ AnomalyAlerts       ← alert cards with resolve button
  └─ WebSocket live feed ← "Live" indicator, updates every 5s
```

---

## Quick Start

### 1. Clone & run

```bash
git clone https://github.com/yourusername/pulseboard
cd pulseboard
docker-compose up --build
```

- **Dashboard:** http://localhost:3000
- **API docs:** http://localhost:8000/docs

### 2. Register & create a project

1. Open http://localhost:3000 → Register
2. Click "New project" → copy your **API Key**

### 3. Instrument your app

```bash
pip install -e ./sdk
```

```python
from fastapi import FastAPI
from pulseboard_sdk import PulseBoardMiddleware

app = FastAPI()

app.add_middleware(
    PulseBoardMiddleware,
    api_key="YOUR_PROJECT_API_KEY",
    base_url="http://localhost:8000",
)

@app.get("/users")
def get_users():
    return [{"id": 1, "name": "Alice"}]
```

Every request to your app now appears live in PulseBoard.

---

## How Anomaly Detection Works

PulseBoard uses **Z-score statistical analysis** — no ML framework required:

1. Every hour, the aggregator computes per-endpoint: avg latency, p95/p99, error rate, request count.
2. These are stored as `HourlyMetric` rows in PostgreSQL.
3. When a new hour is aggregated, the last 24 rows are pulled for each endpoint.
4. A Z-score is computed: `z = (current_value - historical_mean) / historical_std`
5. If `z > 2.5` → **warning alert**. If `z > 5.0` → **critical alert**.
6. Hard threshold: error rate > 10% always triggers critical.

This is intentionally simple, explainable, and effective — exactly what you want in an interview.

---

## Project Structure

```
PulseBoard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, CORS
│   │   ├── config.py            # pydantic-settings (env vars)
│   │   ├── database.py          # PostgreSQL (SQLAlchemy async) + MongoDB (Motor)
│   │   ├── models/
│   │   │   └── postgres_models.py  # User, Project, HourlyMetric, AnomalyAlert
│   │   ├── schemas/
│   │   │   └── events.py        # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── auth.py          # register, login, JWT, projects CRUD
│   │   │   ├── ingest.py        # POST /ingest/event, POST /ingest/batch
│   │   │   └── analytics.py     # metrics, alerts, summary, WebSocket
│   │   └── services/
│   │       ├── anomaly.py       # Z-score detection logic
│   │       └── aggregator.py    # MongoDB → PostgreSQL aggregation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router, auth page, project sidebar
│   │   ├── components/
│   │   │   ├── Dashboard.jsx    # Main dashboard with auto-refresh + WebSocket
│   │   │   ├── SummaryCards.jsx # 4 KPI cards
│   │   │   ├── MetricsChart.jsx # Recharts line + bar charts
│   │   │   └── AnomalyAlerts.jsx# Alert cards with resolve
│   │   └── services/api.js      # Axios + WebSocket helpers
│   └── Dockerfile
├── sdk/
│   ├── pulseboard_sdk/
│   │   ├── tracker.py           # ASGI middleware + batched client
│   │   └── __init__.py
│   └── setup.py                 # pip install -e ./sdk
└── docker-compose.yml           # One command to run everything
```

---

## Resume Talking Points

- **Designed dual-database architecture**: MongoDB for high-write raw events (schema-flexible), PostgreSQL for structured aggregated metrics and relational queries.
- **Built real-time WebSocket feed**: Live dashboard updates every 5 seconds without polling.
- **Implemented statistical anomaly detection** from scratch using Z-score analysis across 24h rolling windows — no ML library dependency.
- **Created a pip-installable Python SDK** with batching, retry logic, and zero-overhead ASGI middleware.
- **Containerized full stack** with Docker Compose: FastAPI + PostgreSQL + MongoDB + Redis + React, one-command setup.
- **Async-first backend**: FastAPI with asyncpg (PostgreSQL) and Motor (MongoDB) — non-blocking I/O throughout.
"# TraceForge" 
"# PulseBoard" 
