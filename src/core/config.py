# Core configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    DB_ADMIN_URL: str
    SECRET_KEY: str
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
