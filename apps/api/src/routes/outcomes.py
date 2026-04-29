from fastapi import APIRouter

router = APIRouter()


@router.post("/upload")
async def upload_outcomes():
    """Upload yesterday's actuals (attended/no_show/cancelled). Week 6."""
    return {"status": "not_implemented"}


@router.get("/metrics")
async def get_metrics():
    """Daily AUC, calibration, drift alerts. Week 6."""
    return {"status": "not_implemented"}
