"""
Configuration management for the application.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Telematics Insurance System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://insurance_user:insurance_pass@postgres:5432/telematics_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_CONSUMER_GROUP: str = "telematics-consumers"
    SCHEMA_REGISTRY_URL: str = "http://schema-registry:8081"

    # Kafka Topics
    KAFKA_TOPIC_RAW: str = "telematics-raw"
    KAFKA_TOPIC_ENRICHED: str = "telematics-enriched"
    KAFKA_TOPIC_RISK_EVENTS: str = "risk-events"
    KAFKA_TOPIC_TRIPS: str = "trip-aggregated"

    # ML Model
    MODEL_PATH: str = "/models/risk_scoring"
    MODEL_VERSION: str = "v1.0"

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 100  # requests per minute

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000", "*"]  # Allow all for demo

    # Feature Store (Redis) TTL
    FEATURE_STORE_TTL_SECONDS: int = 86400  # 24 hours

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
