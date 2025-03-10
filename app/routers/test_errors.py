"""
Test Errors Router

This module provides endpoints for testing error handling in the API.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any

from app.models.database import get_db

router = APIRouter(
    prefix="/test-errors",
    tags=["test-errors"],
    responses={404: {"description": "Not found"}},
)

@router.get("/http-error")
def test_http_error():
    """
    Test HTTP exception handling.
    
    Raises:
        HTTPException: A 404 Not Found error
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="This is a test HTTP error"
    )

@router.get("/database-error")
def test_database_error(db: Session = Depends(get_db)):
    """
    Test database error handling.
    
    Raises:
        SQLAlchemyError: A database error
    """
    # Simulate a database error
    raise SQLAlchemyError("This is a test database error")

@router.get("/value-error")
def test_value_error():
    """
    Test value error handling.
    
    Raises:
        ValueError: A value error
    """
    raise ValueError("This is a test value error")

@router.get("/unexpected-error")
def test_unexpected_error():
    """
    Test unexpected error handling.
    
    Raises:
        Exception: An unexpected error
    """
    # Simulate an unexpected error
    raise Exception("This is a test unexpected error")

@router.get("/validation-error")
def test_validation_error(param: int):
    """
    Test validation error handling.
    
    Args:
        param: An integer parameter
        
    Returns:
        Dict: A success message
    """
    return {"message": f"Parameter value: {param}"}

@router.get("/success")
def test_success() -> Dict[str, Any]:
    """
    Test successful response.
    
    Returns:
        Dict: A success message
    """
    return {"message": "This is a successful response"}

@router.get("/complex-error")
def test_complex_error():
    """
    Test complex error handling that might crash the server.
    
    Raises:
        Exception: A more complex error with nested information
    """
    # Definir la clase de error personalizado fuera de la función
    # para evitar problemas con los closures
    class CustomError(Exception):
        def __init__(self, message, data):
            self.message = message
            self.data = data
            super().__init__(self.message)
            
        def __str__(self):
            # Implementación segura de __str__ para evitar problemas con datos no serializables
            try:
                # Intentar crear una representación segura de los datos
                safe_data = {
                    key: "<<función no serializable>>" if callable(value) else value
                    for key, value in self.data.items()
                }
                return f"{self.message} - Data: {safe_data}"
            except Exception:
                # Si hay algún problema, devolver solo el mensaje
                return self.message
    
    # Crear una estructura de datos compleja, pero más segura
    # Evitar incluir funciones lambda directamente
    complex_data = {
        "nested_data": [1, 2, 3],
        "function_name": "una_función_multiplicadora",
        "description": "Esta función multiplica por 2"
    }
    
    # Lanzar un error personalizado con datos complejos
    raise CustomError(
        "This is a complex error that might crash the server",
        complex_data
    ) 