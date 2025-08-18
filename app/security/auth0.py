"""
Auth0 Security Utilities

Provides FastAPI dependencies to validate Auth0-issued JWTs (RS256) and
extract the current user. Configure via environment variables:

Required:
- AUTH0_DOMAIN (e.g., your-tenant.us.auth0.com)
- AUTH0_AUDIENCE (API identifier configured in Auth0)

Optional:
- AUTH0_ALGORITHMS (default: RS256)
"""

import os
import time
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt


ALGORITHMS = os.getenv("AUTH0_ALGORITHMS", "RS256").split(",")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
    # Keep import-time validation lenient so tests or non-secured contexts can run,
    # but raise at request-time if dependency is used without proper config.
    pass


def _issuer() -> str:
    if not AUTH0_DOMAIN:
        raise RuntimeError("AUTH0_DOMAIN is not configured")
    return f"https://{AUTH0_DOMAIN}/"


@lru_cache(maxsize=1)
def _jwks_cached() -> Dict[str, Any]:
    # Cached JWKS; process restarts refresh the cache. For long-lived processes,
    # consider time-based invalidation if rotating keys frequently.
    jwks_url = f"{_issuer()}.well-known/jwks.json"
    with httpx.Client(timeout=5.0) as client:
        resp = client.get(jwks_url)
        resp.raise_for_status()
        return resp.json()


class User:
    def __init__(self, claims: Dict[str, Any]):
        self.claims = claims
        self.sub: str = claims.get("sub", "")
        self.email: Optional[str] = claims.get("email")
        self.scope: Optional[str] = claims.get("scope")
        self.permissions: Optional[Any] = claims.get("permissions")


bearer_scheme = HTTPBearer(auto_error=False)


def _validate_env():
    if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth0 not configured (missing AUTH0_DOMAIN or AUTH0_AUDIENCE)",
        )


def _get_signing_key(token: str) -> Dict[str, Any]:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Invalid token header: missing kid")
    jwks = _jwks_cached()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(status_code=401, detail="Appropriate JWK not found")


def _decode_token(token: str) -> Dict[str, Any]:
    signing_key = _get_signing_key(token)
    issuer = _issuer()
    return jwt.decode(
        token,
        signing_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer=issuer,
        options={"verify_at_hash": False},
    )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    _validate_env()
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = credentials.credentials
    try:
        claims = _decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    return User(claims)

