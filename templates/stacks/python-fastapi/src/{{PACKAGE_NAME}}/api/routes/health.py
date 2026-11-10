import time
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(tags=["health"])

_START_TIME = time.time()


@router.get("/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }
