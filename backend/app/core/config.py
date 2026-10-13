from pydantic_settings import BaseSettings
from typing import List, Optional
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
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    # Gemini AI (for future stages)
    GEMINI_API_KEY: Optional[str] = None
    
    # Kafka (for future stages)
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = "localhost:9092"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()
