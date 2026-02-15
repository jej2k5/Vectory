"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings populated from environment variables.

    All values have sensible defaults suitable for local development.
    Production deployments MUST override security-sensitive values
    (JWT_SECRET, JWT_REFRESH_SECRET, database credentials, etc.).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://vectoruser:vectorpass@localhost:5432/vectory"

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── MinIO / S3 ────────────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "vectory-uploads"

    # ── JWT ────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "your-super-secret-jwt-key-change-me-min-32-characters"
    JWT_REFRESH_SECRET: str = "your-refresh-secret-key-change-me-min-32-characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Embedding Provider API Keys ───────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    COHERE_API_KEY: str = ""

    # ── Default Embedding Settings ────────────────────────────────────────
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    DEFAULT_DIMENSION: int = 1536
    DEFAULT_DISTANCE_METRIC: str = "cosine"

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # ── Rate Limiting & Upload ────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_UPLOAD_SIZE_MB: int = 100

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = "info"

    # ── Derived helpers ───────────────────────────────────────────────────

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list, split on commas."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        """Return the DATABASE_URL rewritten for asyncpg.

        Converts ``postgresql://`` or ``postgresql+psycopg2://`` to
        ``postgresql+asyncpg://``.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Return the DATABASE_URL rewritten for psycopg2 (used by Celery workers)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


# Singleton – import this wherever settings are needed.
settings = Settings()
