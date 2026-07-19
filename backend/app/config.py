from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_URL: str = "postgresql+asyncpg://pulse:pulse@postgres:5432/pulsedb"

    # MongoDB
    MONGO_URL: str = "mongodb://mongo:27017"
    MONGO_DB: str = "pulsedb"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Auth
    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    class Config:
        env_file = ".env"


settings = Settings()
