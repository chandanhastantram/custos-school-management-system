"""
CUSTOS Auth Package

Authentication and authorization components.
"""

from app.auth.jwt import (
    TokenPayload,
    TokenPair,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_access_token,
    verify_refresh_token,
)

from app.auth.password import (
    hash_password,
    verify_password,
    needs_rehash,
    PasswordValidator,
    password_validator,
)

from app.auth.rbac import (
    SystemRole,
    Permission,
    ROLE_HIERARCHY,
    ROLE_PERMISSIONS,
    check_permission,
    check_any_permission,
    check_all_permissions,
    get_role_level,
    can_manage_role,
    get_default_permissions,
)

from app.auth.dependencies import (
    CurrentUser,
    TenantContext,
    get_current_user,
    get_current_user_optional,
    get_tenant_context,
    require_permissions,
    require_any_permission,
    require_roles,
    require_admin,
    require_super_admin,
    AuthUser,
    OptionalUser,
    TenantCtx,
)

__all__ = [
    # JWT
    "TokenPayload", "TokenPair",
    "create_access_token", "create_refresh_token", "create_token_pair",
    "decode_token", "verify_access_token", "verify_refresh_token",
    # Password
    "hash_password", "verify_password", "needs_rehash",
    "PasswordValidator", "password_validator",
    # RBAC
    "SystemRole", "Permission", "ROLE_HIERARCHY", "ROLE_PERMISSIONS",
    "check_permission", "check_any_permission", "check_all_permissions",
    "get_role_level", "can_manage_role", "get_default_permissions",
    # Dependencies
    "CurrentUser", "TenantContext",
    "get_current_user", "get_current_user_optional", "get_tenant_context",
    "require_permissions", "require_any_permission", "require_roles",
    "require_admin", "require_super_admin",
    "AuthUser", "OptionalUser", "TenantCtx",
]
