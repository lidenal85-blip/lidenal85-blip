from fastapi import FastAPI
import threading
import structlog

from survey_finder.health.health import router as health_router
from survey_finder.logging.logger import init_logger
from survey_finder.coordination.leader import LeaderElectionService
from survey_finder.runtime.execution_controller import ExecutionController

logger = init_logger()
log = structlog.get_logger()

leader_service = LeaderElectionService()
controller = ExecutionController(leader_service)

def create_app() -> FastAPI:
    app = FastAPI(title="Survey Finder")

    app.include_router(health_router)

    @app.on_event("startup")
    def startup():
        leader_service.start()
        threading.Thread(target=controller.run, daemon=True).start()
        log.info("system_started")

    @app.get("/leader")
    def leader_status():
        return {
            "is_leader": leader_service.is_leader(),
            "instance_id": controller.instance_id
        }

    return app

app = create_app()
