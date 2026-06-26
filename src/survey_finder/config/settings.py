from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Infrastructure
    POSTGRES_DSN: str = "postgresql://postgres:postgres@localhost:5432/survey"
    REDIS_URL: str = "redis://localhost:6379"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Nimble Web API (residential proxy scraping)
    NIMBLE_API_KEY: str = ""
    NIMBLE_API_URL: str = "https://api.nimbleway.com/v1/pipeline"

    # Scheduler
    POLL_INTERVAL_SECONDS: int = 300   # 5 min default
    POLL_SOURCES: str = "prolific,cloudresearch,respondent"

settings = Settings()
