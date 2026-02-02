"""
CUSTOS Health Check Router

System health endpoints including resilience status.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.resilience import (
    get_resilience_health,
    get_all_circuit_status,
)
from app.core.cache import get_cache

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "custos",
        "version": "2.0.0",
    }


@router.get("/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including:
    - Database connection
    - Cache status
    - Circuit breaker status
    """
    health = {
        "status": "healthy",
        "checks": {},
    }
    
    # Database check
    try:
        await db.execute("SELECT 1")
        health["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)[:100],
        }
        health["status"] = "degraded"
    
    # Cache check
    try:
        cache = await get_cache()
        cache_health = await cache.health_check()
        health["checks"]["cache"] = cache_health
        if cache_health.get("status") != "healthy":
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)[:100],
        }
    
    # Resilience check
    try:
        resilience = get_resilience_health()
        health["checks"]["resilience"] = resilience
        if resilience.get("status") != "healthy":
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["resilience"] = {
            "status": "error",
            "error": str(e)[:100],
        }
    
    return health


@router.get("/circuits")
async def circuit_status():
    """
    Get status of all circuit breakers.
    
    Shows which features are in degraded mode.
    """
    return {
        "circuits": get_all_circuit_status(),
        "summary": get_resilience_health(),
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if ready to serve traffic, 503 otherwise.
    """
    try:
        await db.execute("SELECT 1")
        return {"ready": True}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Not ready")


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if process is alive.
    """
    return {"alive": True}
