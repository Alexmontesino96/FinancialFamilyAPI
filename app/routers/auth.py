"""
Auth Router (Auth0)

Token issuance is handled by Auth0. This router exposes a simple
endpoint to retrieve the current authenticated user's basic profile
from the validated JWT.
"""

from fastapi import APIRouter, Depends

from app.security.auth0 import User, get_current_user
from app.utils.logging_config import get_logger

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)


@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's claims (subset)."""
    logger.info(f"Auth0 user: {current_user.sub}")
    return {
        "sub": current_user.sub,
        "email": current_user.email,
        "scope": current_user.scope,
        "permissions": current_user.permissions,
    }
