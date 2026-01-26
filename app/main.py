"""
CUSTOS Main Application

FastAPI application entry point.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.core.exceptions import CustosException
from app.api.v1 import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 Environment: {settings.environment}")
    print(f"📝 Debug: {settings.debug}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    await engine.dispose()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        description="""
## CUSTOS - AI-Powered School Management System

A comprehensive SaaS platform for educational institutions featuring:

- 🏫 **Multi-tenant Architecture** - Complete data isolation per school
- 👥 **Role-Based Access Control** - Flexible permissions for all user types
- 📚 **Academic Management** - Classes, sections, subjects, syllabus, lessons
- ❓ **Question Bank** - AI-powered question generation with Bloom's taxonomy
- 📝 **Assignments & Worksheets** - Create, distribute, and grade work
- ✅ **Manual Correction Workflow** - Spreadsheet-style grading interface
- 🤖 **AI Features** - Lesson plans, question generation, doubt solving
- 📊 **Analytics & Reports** - Student, class, and teacher performance
- 💳 **SaaS Billing** - Plans, subscriptions, and usage limits
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Exception handlers
    @app.exception_handler(CustosException)
    async def custos_exception_handler(request: Request, exc: CustosException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        if settings.debug:
            import traceback
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": str(exc),
                    "code": "INTERNAL_ERROR",
                    "details": {"traceback": traceback.format_exc()},
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    
    # API info endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "AI-Powered School Management System",
            "docs": "/docs" if settings.debug else None,
            "api": "/api/v1",
        }
    
    # Include API routers
    app.include_router(v1_router, prefix="/api")
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else 4,
    )
