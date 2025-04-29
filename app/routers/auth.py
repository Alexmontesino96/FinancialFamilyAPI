"""
Auth Router

This module defines the endpoints for authentication in the API.
It provides routes for validating user credentials and generating token for members.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.models.database import get_db
from app.models.schemas import Token
from app.services.member_service import MemberService
from app.services.token_service import create_access_token
from app.utils.logging_config import get_logger

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Generate an access token for a member.
    
    Args:
        form_data: OAuth2 form with username and password
        db: Database session
        
    Returns:
        Token: An OAuth2 compatible token
        
    Raises:
        HTTPException: If authentication fails
    """
    logger.info(f"Auth attempt for username: {form_data.username}")
    
    # Buscar al miembro por su telegram_id (que usamos como username)
    member = MemberService.get_member_by_telegram_id(db, form_data.username)
    
    # La autenticación actual usa solo telegram_id sin verificar contraseña
    # En un sistema real, se debe verificar la contraseña aquí
    if not member:
        logger.warning(f"Authentication failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear un token de acceso usando el telegram_id como sub (subject)
    access_token = create_access_token(data={"sub": member.telegram_id})
    
    logger.info(f"Authentication successful for username: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"} 