"""
CUSTOS Health Check Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings


router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """Database health check."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check for Kubernetes."""
    checks = {
        "database": False,
    }
    
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    
    is_ready = all(checks.values())
    
    return {
        "ready": is_ready,
        "checks": checks,
    }


@router.get("/health/resilience")
async def resilience_health():
    """
    Get resilience status including circuit breakers.
    
    Shows which features are degraded/unavailable.
    """
    from app.core.resilience import get_resilience_health, get_all_circuit_status
    
    return {
        "summary": get_resilience_health(),
        "circuits": get_all_circuit_status(),
    }


@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including:
    - Database connection
    - Cache status
    - Circuit breaker status
    """
    from app.core.resilience import get_resilience_health
    from app.core.cache import get_cache
    
    health = {
        "status": "healthy",
        "checks": {},
    }
    
    # Database check
    try:
        await db.execute(text("SELECT 1"))
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
        if cache_health.get("status") not in ("healthy", "unavailable"):
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["cache"] = {
            "status": "error",
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

