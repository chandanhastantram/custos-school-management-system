"""
CUSTOS - AI-Powered School Management System

Main FastAPI application.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

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

# Frontend dist path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()  # Auto-create tables on startup
    
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
        allow_origins=settings.allowed_origins_list,
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
    
    # API Routers (must be registered BEFORE static files)
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api")
    
    # Serve frontend static files (if dist directory exists)
    if FRONTEND_DIR.exists():
        logger.info(f"Serving frontend from: {FRONTEND_DIR}")
        
        # Mount static assets (JS, CSS, images)
        assets_dir = FRONTEND_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")
        
        # Serve root-level static files (favicon, robots.txt, etc.)
        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            favicon_path = FRONTEND_DIR / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(str(favicon_path))
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        @app.get("/robots.txt", include_in_schema=False)
        async def robots():
            robots_path = FRONTEND_DIR / "robots.txt"
            if robots_path.exists():
                return FileResponse(str(robots_path))
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        # SPA fallback: serve index.html for all unmatched routes
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(request: Request, full_path: str):
            """Serve the React SPA for any non-API route."""
            # Don't catch API routes
            if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
                return JSONResponse(status_code=404, content={"detail": "Not Found"})
            
            # Check if it's a static file in dist
            file_path = FRONTEND_DIR / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            
            # Fallback to index.html for SPA routing
            index_path = FRONTEND_DIR / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path), media_type="text/html")
            
            return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
    else:
        logger.warning(f"Frontend dist not found at {FRONTEND_DIR}. Only API will be served.")
        
        @app.get("/", include_in_schema=False)
        async def root():
            return {
                "name": settings.app_name,
                "version": settings.app_version,
                "docs": "/docs" if settings.debug else None,
                "api": "/api/v1",
                "health": "/health",
            }
    
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

