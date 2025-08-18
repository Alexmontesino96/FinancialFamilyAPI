"""
Legacy auth module adapted to Auth0.

This module re-exports Auth0-based dependencies to preserve import paths
if other modules refer to app.auth.auth.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.security.auth0 import get_current_user, User  # noqa: F401
from app.models.database import get_db  # noqa: F401

# Backwards-compatible alias
async def get_current_active_member(current_user: User = Depends(get_current_user)) -> User:  # noqa: D401
    """Return the current authenticated user (Auth0)."""
    return current_user
