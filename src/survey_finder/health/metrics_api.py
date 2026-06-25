from fastapi import APIRouter
from survey_finder.runtime.metrics import Metrics

router = APIRouter()
metrics = Metrics()

@router.get("/metrics")
def metrics_snapshot():
    return metrics.snapshot()
