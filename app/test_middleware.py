"""
Test Middleware Script

This script tests the error handling middleware by simulating different types of errors.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any

from app.middlewares.error_handler import ErrorHandler
from app.middlewares.http_exception_handler import http_exception_handler, validation_exception_handler

# Initialize FastAPI application
app = FastAPI(
    title="Test Middleware API",
    description="API for testing error handling middleware",
    version="1.0.0"
)

# Add error handling middleware
app.add_middleware(ErrorHandler)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    Root endpoint.
    
    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to the Test Middleware API"}

@app.get("/http-error")
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

@app.get("/database-error")
def test_database_error():
    """
    Test database error handling.
    
    Raises:
        SQLAlchemyError: A database error
    """
    # Simulate a database error
    raise SQLAlchemyError("This is a test database error")

@app.get("/value-error")
def test_value_error():
    """
    Test value error handling.
    
    Raises:
        ValueError: A value error
    """
    raise ValueError("This is a test value error")

@app.get("/unexpected-error")
def test_unexpected_error():
    """
    Test unexpected error handling.
    
    Raises:
        Exception: An unexpected error
    """
    # Simulate an unexpected error
    raise Exception("This is a test unexpected error")

@app.get("/success")
def test_success() -> Dict[str, Any]:
    """
    Test successful response.
    
    Returns:
        Dict: A success message
    """
    return {"message": "This is a successful response"}

# Run the application when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.test_middleware:app", host="0.0.0.0", port=8009, reload=True) 