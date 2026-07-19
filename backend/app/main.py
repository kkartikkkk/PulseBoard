from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base, connect_mongo, disconnect_mongo
from app.routers import auth, ingest, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await connect_mongo()
    yield
    # Shutdown
    await disconnect_mongo()
    await engine.dispose()


app = FastAPI(
    title="PulseBoard API",
    description="Real-Time API Analytics & Anomaly Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(analytics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pulseboard-api"}
