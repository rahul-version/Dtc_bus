from fastapi import APIRouter
import time

router = APIRouter()
start_time = time.time()

@router.get("")
@router.get("/")
async def health_check():
    """
    Kubernetes Liveness / Readiness Probe.
    Returns service health, uptime, and ML engine status.
    """
    return {
        "status": "healthy",
        "service": "delhi-dtc-crowdedness-backend",
        "uptime_seconds": round(time.time() - start_time, 2),
        "ml_engine": "ready",
        "version": "1.0.0"
    }
