from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    POSTGRES_DSN: str
    REDIS_URL: str
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    class Config:
        env_file = ".env"
settings = Settings()
