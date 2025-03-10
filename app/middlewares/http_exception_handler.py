"""
HTTP Exception Handler

This module provides handlers for HTTP exceptions in the API.
It formats HTTP exceptions to provide consistent error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from typing import Dict, Any, Union, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Args:
        request: The incoming request
        exc: The HTTP exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    logger.warning(f"Request path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            message=exc.detail,
            error_type="http_error",
            status_code=exc.status_code
        )
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation exceptions.
    
    Args:
        request: The incoming request
        exc: The validation exception
        
    Returns:
        JSONResponse: Formatted error response with validation details
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        }
        errors.append(error_detail)
    
    logger.warning(f"Validation error: {errors}")
    logger.warning(f"Request path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            message="Validation error",
            error_type="validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors
        )
    )

def format_error_response(
    message: str, 
    error_type: str, 
    status_code: int,
    errors: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format the error response.
    
    Args:
        message: Error message
        error_type: Type of error
        status_code: HTTP status code
        errors: Optional list of detailed errors
        
    Returns:
        Dict: Formatted error response
    """
    response = {
        "error": {
            "message": message,
            "type": error_type,
            "status_code": status_code
        }
    }
    
    if errors:
        response["error"]["details"] = errors
    
    return response 