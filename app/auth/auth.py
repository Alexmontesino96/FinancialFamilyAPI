from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.models.database import get_db
from app.models.models import Member
from app.models.schemas import TokenData

# Cargar variables de entorno
load_dotenv()

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_member(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene el miembro actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        telegram_id: str = payload.get("sub")
        if telegram_id is None:
            raise credentials_exception
        token_data = TokenData(username=telegram_id)
    except JWTError:
        raise credentials_exception
    
    member = db.query(Member).filter(Member.telegram_id == token_data.username).first()
    if member is None:
        raise credentials_exception
    return member

async def get_current_active_member(current_member: Member = Depends(get_current_member)):
    """Obtiene el miembro actual y verifica que esté activo."""
    return current_member

def authenticate_member(telegram_id: str, db: Session):
    """Autentica a un miembro por su ID de Telegram."""
    member = db.query(Member).filter(Member.telegram_id == telegram_id).first()
    return member 