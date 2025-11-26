"""
RBAC Manager - Role-Based Access Control.
"""
from typing import Dict, Set
from enum import Enum

from feniks.logger import get_logger
from feniks.security.auth import UserRole

log = get_logger("security.rbac")


class Permission(Enum):
    """System permissions."""
    # Read permissions
    VIEW_METRICS = "view_metrics"
    VIEW_REPORTS = "view_reports"
    VIEW_PROJECTS = "view_projects"

    # Write permissions
    INGEST_CODE = "ingest_code"
    ANALYZE_CODE = "analyze_code"
    REFACTOR_CODE = "refactor_code"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_PROJECTS = "manage_projects"
    MANAGE_BUDGETS = "manage_budgets"
    VIEW_ALL_METRICS = "view_all_metrics"


class RBACManager:
    """
    Manages role-based access control.

    Defines permissions for each role:
    - VIEWER: Read-only access to metrics and reports
    - REFACTORER: Can ingest, analyze, and refactor code
    - ADMIN: Full system access
    """

    def __init__(self):
        """Initialize RBAC manager."""
        self.role_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.VIEWER: {
                Permission.VIEW_METRICS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_PROJECTS
            },
            UserRole.REFACTORER: {
                Permission.VIEW_METRICS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_PROJECTS,
                Permission.INGEST_CODE,
                Permission.ANALYZE_CODE,
                Permission.REFACTOR_CODE
            },
            UserRole.ADMIN: set(Permission)  # All permissions
        }
        log.info("RBACManager initialized")

    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        """
        Check if role has permission.

        Args:
            role: User role
            permission: Permission to check

        Returns:
            bool: True if role has permission
        """
        return permission in self.role_permissions.get(role, set())

    def get_role_permissions(self, role: UserRole) -> Set[Permission]:
        """
        Get all permissions for a role.

        Args:
            role: User role

        Returns:
            Set of permissions
        """
        return self.role_permissions.get(role, set())
