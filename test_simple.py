"""
Simple Test Script

This script tests FastAPI without custom middlewares.
"""

from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any

# Initialize FastAPI application
app = FastAPI(
    title="Simple Test API",
    description="API for testing FastAPI",
    version="1.0.0"
)

@app.get("/")
def read_root():
    """
    Root endpoint.
    
    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to the Simple Test API"}

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
    uvicorn.run("test_simple:app", host="0.0.0.0", port=8010, reload=True) 