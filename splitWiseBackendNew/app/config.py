import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT_DIR, '.env')

if os.path.exists(ENV_FILE_PATH):
    load_dotenv(ENV_FILE_PATH)

class AppSettings(BaseSettings):
    PROJECT_NAME: str = "Minimal Splitwise API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./default_minimal_app.db" 
    SECRET_KEY: str = "default_secret_key_change_this" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    CACHE_EXPIRATION_SECONDS: int = 300 # 5 minutes

    class Config:
        case_sensitive = True

settings = AppSettings()