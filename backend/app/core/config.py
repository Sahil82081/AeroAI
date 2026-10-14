from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AeroAI: Autonomous Disruption Recovery System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "super-secret-dev-key-change-in-production-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database
    # Default to sqlite local fallback if postgres isn't running immediately on localhost
    DATABASE_URL: str = "sqlite:///./autonomous_recovery.db"
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "disruption_recovery"
    POSTGRES_PORT: Optional[int] = 5432
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Gemini AI (for future stages)
    GEMINI_API_KEY: Optional[str] = None
    
    # Kafka (for future stages)
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = "localhost:9092"
    
    # Live News Feed Configuration (Google News RSS)
    NEWS_FEED_URL: str = "https://news.google.com/rss/search"
    NEWS_FEED_REGION: str = "IN"
    NEWS_FEED_LANGUAGE: str = "en-IN"
    NEWS_FEED_CEID: str = "IN:en"
    NEWS_CACHE_TTL_SECONDS: int = 900  # 15 minutes TTL
    NEWS_TIMEOUT_SECONDS: float = 10.0
    
    # Airline Policy Knowledge Base & RAG Configuration
    POLICIES_RAW_DIR: str = "data/policies/raw"
    POLICIES_DB_DIR: str = "data/policies/chroma_db"
    POLICIES_MANIFEST_PATH: str = "data/policies/sources.json"
    POLICIES_INGESTION_MANIFEST: str = "data/policies/ingestion_manifest.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
