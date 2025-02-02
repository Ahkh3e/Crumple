from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, HttpUrl

class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Crumple"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5000"]
    
    # PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "crumple"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT", 5432)),
            path=f"/{values.get('POSTGRES_DB', '')}",
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # WebSocket
    WS_MESSAGE_QUEUE: str = "redis://localhost:6379/1"
    
    # NetBox Integration
    NETBOX_SYNC_INTERVAL: int = 300  # seconds
    NETBOX_WEBHOOK_SECRET: Optional[str] = None
    NETBOX_BATCH_SIZE: int = 100  # items per sync batch
    NETBOX_MAX_RETRIES: int = 3
    NETBOX_RETRY_DELAY: int = 60  # seconds
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5000"
    
    # Topology Settings
    MAX_DEVICES_PER_CLUSTER: int = 1000
    MAX_CONNECTIONS_PER_DEVICE: int = 100
    ALLOWED_CABLE_TYPES: List[str] = [
        "cat6", "cat6a", "cat7",
        "mmf", "smf",
        "aoc", "dac",
        "nvlink"
    ]
    
    # Performance
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    CACHE_TTL: int = 300  # seconds
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create global settings object
settings = Settings()
