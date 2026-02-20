# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Authentication Manager - Handles JWT authentication and user management.
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

import jwt

from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("security.auth")


class UserRole(Enum):
    """User roles for RBAC."""

    VIEWER = "viewer"  # Read-only access
    REFACTORER = "refactorer"  # Can generate refactorings
    ADMIN = "admin"  # Full access


@dataclass
class User:
    """Represents an authenticated user."""

    user_id: str
    username: str
    email: str
    role: UserRole
    projects: list[str]  # List of accessible project IDs
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AuthenticationError(FeniksError):
    """Exception for authentication failures."""

    pass


class AuthorizationError(FeniksError):
    """Exception for authorization failures."""

    pass


class AuthManager:
    """
    Manages authentication using JWT tokens and API keys.

    Supports:
    - JWT token validation
    - API key authentication
    - Role-based access control
    - Multi-tenant project access
    """

    def __init__(self, jwt_secret: Optional[str] = None, jwt_algorithm: str = "HS256", token_expiry_hours: int = 24):
        """
        Initialize auth manager.

        Args:
            jwt_secret: Secret key for JWT signing
            jwt_algorithm: JWT algorithm (default: HS256)
            token_expiry_hours: Token expiration time in hours
        """
        self.jwt_secret = jwt_secret or self._generate_default_secret()
        self.jwt_algorithm = jwt_algorithm
        self.token_expiry_hours = token_expiry_hours

        # In-memory API key store (in production, use database)
        self.api_keys: Dict[str, User] = {}

        log.info("AuthManager initialized")

    def _generate_default_secret(self) -> str:
        """Generate a default JWT secret (for development only)."""
        log.warning("Using default JWT secret. Set JWT_SECRET in production!")
        return "feniks-default-secret-change-in-production"

    def generate_token(self, user: User) -> str:
        """
        Generate JWT token for a user.

        Args:
            user: User to generate token for

        Returns:
            str: JWT token
        """
        expiry = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)

        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "projects": user.projects,
            "exp": expiry,
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        log.info(f"Generated token for user: {user.username}")
        return token

    def validate_token(self, token: str) -> User:
        """
        Validate JWT token and extract user.

        Args:
            token: JWT token to validate

        Returns:
            User: Authenticated user

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            user = User(
                user_id=payload["user_id"],
                username=payload["username"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                projects=payload.get("projects", []),
            )

            log.debug(f"Validated token for user: {user.username}")
            return user

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    def create_api_key(self, user: User) -> str:
        """
        Create API key for a user.

        Args:
            user: User to create API key for

        Returns:
            str: API key
        """
        # Generate API key using hash
        key_data = f"{user.user_id}:{user.username}:{datetime.utcnow().isoformat()}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()

        # Store mapping
        self.api_keys[api_key] = user

        log.info(f"Created API key for user: {user.username}")
        return api_key

    def validate_api_key(self, api_key: str) -> User:
        """
        Validate API key and get user.

        Args:
            api_key: API key to validate

        Returns:
            User: Authenticated user

        Raises:
            AuthenticationError: If API key is invalid
        """
        user = self.api_keys.get(api_key)
        if not user:
            raise AuthenticationError("Invalid API key")

        log.debug(f"Validated API key for user: {user.username}")
        return user

    def authenticate(self, credentials: str) -> User:
        """
        Authenticate using either JWT token or API key.

        Args:
            credentials: JWT token or API key

        Returns:
            User: Authenticated user

        Raises:
            AuthenticationError: If authentication fails
        """
        # Try JWT first
        if credentials.startswith("Bearer ") or len(credentials) > 100:
            try:
                return self.validate_token(credentials)
            except AuthenticationError:
                pass

        # Try API key
        return self.validate_api_key(credentials)

    def check_permission(self, user: User, operation: str, project_id: Optional[str] = None) -> bool:
        """
        Check if user has permission for operation.

        Args:
            user: User to check
            operation: Operation name (e.g., 'ingest', 'analyze', 'refactor')
            project_id: Optional project ID

        Returns:
            bool: True if user has permission

        Raises:
            AuthorizationError: If permission denied
        """
        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Check project access if specified
        if project_id and project_id not in user.projects:
            raise AuthorizationError(f"User {user.username} has no access to project {project_id}")

        # Role-based permissions
        if operation in ["ingest", "analyze"]:
            # Viewers, refactorers, and admins can read
            return True

        if operation == "refactor":
            # Only refactorers and admins can refactor
            if user.role not in [UserRole.REFACTORER, UserRole.ADMIN]:
                raise AuthorizationError(f"User {user.username} does not have refactor permission")
            return True

        if operation in ["config", "manage_users", "manage_budgets"]:
            # Only admins can manage system
            if user.role != UserRole.ADMIN:
                raise AuthorizationError(f"User {user.username} does not have admin permission")
            return True

        # Unknown operation - deny by default
        raise AuthorizationError(f"Unknown operation: {operation}")


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager(jwt_secret: Optional[str] = None, jwt_algorithm: str = "HS256") -> AuthManager:
    """
    Get global auth manager instance.

    Args:
        jwt_secret: Optional JWT secret (only used on first call)
        jwt_algorithm: JWT algorithm

    Returns:
        AuthManager: Global instance
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(jwt_secret=jwt_secret, jwt_algorithm=jwt_algorithm)
    return _auth_manager
