from fastapi import FastAPI
from survey_finder.health.health import router as health_router
from survey_finder.logging.logger import init_logger

logger = init_logger()

def create_app() -> FastAPI:
    app = FastAPI(title="Survey Finder")

    app.include_router(health_router)

    @app.on_event("startup")
    def startup():
        logger.info("system_starting")

        # lazy init here (IMPORTANT)
        from survey_finder.coordination.bootstrap import get_leader_service
        get_leader_service()

    return app

app = create_app()
