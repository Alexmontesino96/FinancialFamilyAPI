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
    Obtiene un token de acceso para un miembro.
    
    El nombre de usuario debe ser el ID de Telegram del miembro.
    La contraseña puede ser cualquier valor, ya que la autenticación se basa en el ID de Telegram.
    """
    # Autenticar al miembro
    member = authenticate_member(form_data.username, db)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect telegram_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear el token de acceso
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": member.telegram_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 