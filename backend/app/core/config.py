from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Delhi DTC Crowdedness-Aware Journey Planner"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Delhi Transport Stack (DTS) Realtime API Credentials
    DTS_REALTIME_URL: str = "https://dts-backend.transportstack.in/api/dataset/otd/get-file?agency=delhi-buses&category=realtime_gtfs&filename=VehiclePositions.pb"
    DTS_API_KEY: str = "cllu88kOKkri_1j1wMWIjs7509aNCM8nN2nbUE-ZPnY"
    
    # Security & Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 150
    CORS_ORIGINS: List[str] = ["*"]
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Cache settings
    CACHE_TTL_SECONDS: int = 20
    
    class Config:
        case_sensitive = True

settings = Settings()
