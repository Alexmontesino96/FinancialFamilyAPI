"""
Authentication Module

This module handles JWT-based authentication for the API. It provides functions
for creating access tokens, validating tokens, and retrieving the current authenticated
member from a token.

The module uses Telegram IDs as the primary authentication mechanism, without requiring
passwords, as authentication is delegated to the Telegram platform.
"""

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

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing configuration (not actively used since we authenticate via Telegram)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data (dict): Data to encode in the token, should include a 'sub' key with the Telegram ID
        expires_delta (Optional[timedelta]): Custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
    
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_member(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the current authenticated member from a JWT token.
    
    This function is used as a dependency in protected endpoints to validate
    the token and retrieve the corresponding member.
    
    Args:
        token (str): JWT token from the Authorization header
        db (Session): Database session
    
    Returns:
        Member: The authenticated member
    
    Raises:
        HTTPException: If the token is invalid or the member doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        telegram_id: str = payload.get("sub")
        if telegram_id is None:
            raise credentials_exception
        token_data = TokenData(username=telegram_id)
    except JWTError:
        raise credentials_exception
    
    # Find the member in the database
    member = db.query(Member).filter(Member.telegram_id == token_data.username).first()
    if member is None:
        raise credentials_exception
    return member

async def get_current_active_member(current_member: Member = Depends(get_current_member)):
    """
    Get the current active member.
    
    This function is used as a dependency in protected endpoints to ensure
    the authenticated member is active.
    
    Args:
        current_member (Member): The authenticated member from get_current_member
    
    Returns:
        Member: The authenticated active member
    """
    return current_member

def authenticate_member(telegram_id: str, db: Session):
    """
    Authenticate a member by their Telegram ID.
    
    This function is used in the token endpoint to authenticate a member
    and generate a token.
    
    Args:
        telegram_id (str): Telegram ID of the member
        db (Session): Database session
    
    Returns:
        Member: The authenticated member or None if not found
    """
    member = db.query(Member).filter(Member.telegram_id == telegram_id).first()
    return member 