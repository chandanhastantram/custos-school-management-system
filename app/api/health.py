"""
Enhanced Health Check Endpoints

Provides comprehensive health checks for all services.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.cache import cache
import time

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with all services."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "latency_ms": 0  # Could track actual latency
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis cache
    try:
        if cache.redis:
            await cache.redis.ping()
            health_status["services"]["redis"] = {
                "status": "healthy"
            }
        else:
            health_status["services"]["redis"] = {
                "status": "disabled"
            }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503


@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
