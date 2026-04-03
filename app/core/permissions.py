from enum import Enum


class UserRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


# Define what each role can do
ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.VIEWER: {
        "records:read",
        "dashboard:read",
    },
    UserRole.ANALYST: {
        "records:read",
        "dashboard:read",
        "dashboard:insights",
    },
    UserRole.ADMIN: {
        "records:read",
        "records:create",
        "records:update",
        "records:delete",
        "dashboard:read",
        "dashboard:insights",
        "users:read",
        "users:create",
        "users:update",
        "users:delete",
    },
}


def has_permission(role: UserRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())