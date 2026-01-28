"""
CUSTOS - AI-Powered School Management System

Main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.exceptions import CustosException
from app.middleware.tenant import TenantMiddleware
from app.middleware.logging import RequestLoggingMiddleware, setup_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1 import router as v1_router
from app.api.health import router as health_router
from app.api.openapi import OPENAPI_TAGS


# Configure logging with request tracing
setup_logging(debug=settings.debug)
logger = logging.getLogger("custos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    # await init_db()  # Uncomment if you want auto table creation
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# CUSTOS - AI-Powered School Management System

A modern, multi-tenant SaaS platform for educational institutions.

## Features

- 🏫 **Multi-Tenant Architecture** - Complete data isolation per school
- 👥 **User Management** - Students, teachers, parents, admins
- 📚 **Academic Management** - Classes, subjects, syllabus, assignments
- 🤖 **AI-Powered** - Lesson plans, question generation, doubt solver
- 🎮 **Gamification** - Points, badges, leaderboards
- 📊 **Reports** - Student, class, and teacher analytics
- 💳 **SaaS Billing** - Subscription plans and usage tracking

## Authentication

All endpoints (except health checks) require JWT authentication.
Include the token in the `Authorization` header: `Bearer <token>`

## Multi-Tenancy

Include tenant identifier in the `X-Tenant-ID` header for all requests.
        """,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        license_info={
            "name": "Proprietary",
        },
        contact={
            "name": "CUSTOS Support",
            "email": "support@custos.school",
        },
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    
    # Custom middleware (order matters - first added = outermost)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_requests)
    app.add_middleware(TenantMiddleware)
    
    # Exception handlers
    @app.exception_handler(CustosException)
    async def custos_exception_handler(request: Request, exc: CustosException):
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "-")
        logger.exception(f"[{request_id}] Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )
    
    # Routers
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api")
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
