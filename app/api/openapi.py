"""
CUSTOS OpenAPI Configuration

API documentation metadata and schemas.
"""

from typing import List, Dict, Any


# OpenAPI Tags with descriptions
OPENAPI_TAGS: List[Dict[str, Any]] = [
    {
        "name": "Health",
        "description": "Health check and readiness endpoints",
    },
    {
        "name": "Auth",
        "description": "Authentication - login, logout, token refresh, password management",
    },
    {
        "name": "Tenants",
        "description": "School/Institution registration and management",
    },
    {
        "name": "Users",
        "description": "User management - students, teachers, staff, parents",
    },
    {
        "name": "Academic Structure",
        "description": "Academic years, classes, and sections",
    },
    {
        "name": "Questions",
        "description": "Question bank management - create, review, approve",
    },
    {
        "name": "Assignments",
        "description": "Assignments, submissions, and grading",
    },
    {
        "name": "AI",
        "description": "AI-powered features - lesson plans, question generation, doubt solver",
    },
    {
        "name": "Billing",
        "description": "Subscription plans, usage tracking, billing management",
    },
    {
        "name": "Notifications",
        "description": "In-app notifications and alerts",
    },
    {
        "name": "Files",
        "description": "File upload and storage",
    },
    {
        "name": "Gamification",
        "description": "Points, badges, and leaderboards",
    },
    {
        "name": "Reports",
        "description": "Student, class, and teacher performance reports",
    },
    {
        "name": "Platform Admin",
        "description": "Platform-level administration (non-tenant-scoped)",
    },
]


# Common response schemas for OpenAPI
ERROR_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Validation error"},
                        "code": {"type": "string", "example": "VALIDATION_ERROR"},
                        "details": {"type": "object"},
                    },
                },
            },
        },
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Authentication required"},
                        "code": {"type": "string", "example": "AUTHENTICATION_REQUIRED"},
                    },
                },
            },
        },
    },
    402: {
        "description": "Payment Required / Plan Upgrade Needed",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "This feature requires a higher plan"},
                        "code": {"type": "string", "example": "PLAN_UPGRADE_REQUIRED"},
                        "details": {
                            "type": "object",
                            "properties": {
                                "required_plans": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Permission denied"},
                        "code": {"type": "string", "example": "PERMISSION_DENIED"},
                    },
                },
            },
        },
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Resource not found"},
                        "code": {"type": "string", "example": "NOT_FOUND"},
                    },
                },
            },
        },
    },
    409: {
        "description": "Conflict",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Resource already exists"},
                        "code": {"type": "string", "example": "DUPLICATE_ERROR"},
                    },
                },
            },
        },
    },
    429: {
        "description": "Too Many Requests",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Rate limit exceeded"},
                        "code": {"type": "string", "example": "RATE_LIMIT_EXCEEDED"},
                        "details": {
                            "type": "object",
                            "properties": {
                                "retry_after_seconds": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string", "example": "Internal server error"},
                        "code": {"type": "string", "example": "INTERNAL_ERROR"},
                    },
                },
            },
        },
    },
}
