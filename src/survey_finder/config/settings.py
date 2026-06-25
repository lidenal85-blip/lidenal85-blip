from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_DSN: str = "postgresql://postgres:postgres@localhost:5432/survey"
    REDIS_URL: str = "redis://localhost:6379"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
