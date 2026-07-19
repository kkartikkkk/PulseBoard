from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# ── PostgreSQL (SQLAlchemy async) ──────────────────────────────────────────
engine = create_async_engine(settings.POSTGRES_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── MongoDB (Motor async) ──────────────────────────────────────────────────
mongo_client: AsyncIOMotorClient = None


def get_mongo_db():
    return mongo_client[settings.MONGO_DB]


async def connect_mongo():
    global mongo_client
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)


async def disconnect_mongo():
    global mongo_client
    if mongo_client:
        mongo_client.close()
