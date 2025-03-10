"""
Authentication Router

This module defines the authentication endpoints for the API.
It provides routes for obtaining JWT access tokens using Telegram IDs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any

from app.auth.auth import authenticate_member, create_access_token
from app.models.database import get_db
from app.models.schemas import Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get an access token for authentication.
    
    This endpoint authenticates a member using their Telegram ID and issues a JWT token.
    The username field should contain the Telegram ID of the member.
    The password field can be any value, as authentication is based solely on the Telegram ID.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Form containing username (Telegram ID) and password
        db (Session): Database session
    
    Returns:
        Token: Object containing the access token and token type
        
    Raises:
        HTTPException: If authentication fails (Telegram ID not found)
    
    Example:
        ```
        curl -X POST "http://localhost:8007/auth/token" \
             -H "Content-Type: application/x-www-form-urlencoded" \
             -d "username=123456789&password=any_value"
        ```
    """
    # Authenticate the member by Telegram ID
    member = authenticate_member(form_data.username, db)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with 30-minute expiration
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": member.telegram_id}, expires_delta=access_token_expires
    )
    
    # Return token response
    return {"access_token": access_token, "token_type": "bearer"} 