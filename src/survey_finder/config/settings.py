from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_DSN: str
    REDIS_URL: str
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    LEADER_KEY: str = "survey-finder:leader"
    LEADER_TTL_SEC: int = 15
    HEARTBEAT_SEC: int = 5

    # A2.1 runtime
    EXECUTION_LOOP_SLEEP: float = 2.0

    class Config:
        env_file = ".env"

settings = Settings()
