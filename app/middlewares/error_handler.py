"""
Error Handler Middleware

This module provides middleware for handling exceptions in the API.
It catches exceptions and returns appropriate HTTP responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Union
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions in the API.
    
    This middleware catches exceptions raised during request processing
    and returns appropriate HTTP responses with error details.
    """
    
    def __init__(self, app: FastAPI) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and handle any exceptions.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response: Either the normal response or an error response
        """
        try:
            response = await call_next(request)
            return response
        except SQLAlchemyError as e:
            # Database errors
            return self._handle_database_error(e, request)
        except ValueError as e:
            # Value errors (validation, etc.)
            return self._handle_value_error(e, request)
        except Exception as e:
            # Unexpected errors
            return self._handle_unexpected_error(e, request)
    
    def _handle_database_error(self, exc: SQLAlchemyError, request: Request) -> JSONResponse:
        """
        Handle database-related errors.
        
        Args:
            exc: The database exception
            request: The incoming request
            
        Returns:
            JSONResponse: Error response with appropriate status code
        """
        logger.error(f"Database error: {str(exc)}")
        logger.error(f"Request path: {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=self._format_error_response(
                "Database error occurred",
                "database_error",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )
    
    def _handle_value_error(self, exc: ValueError, request: Request) -> JSONResponse:
        """
        Handle value errors (validation, etc.).
        
        Args:
            exc: The value exception
            request: The incoming request
            
        Returns:
            JSONResponse: Error response with appropriate status code
        """
        logger.warning(f"Value error: {str(exc)}")
        logger.warning(f"Request path: {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=self._format_error_response(
                str(exc),
                "value_error",
                status.HTTP_400_BAD_REQUEST
            )
        )
    
    def _handle_unexpected_error(self, exc: Exception, request: Request) -> JSONResponse:
        """
        Handle unexpected errors.
        
        Args:
            exc: The unexpected exception
            request: The incoming request
            
        Returns:
            JSONResponse: Error response with appropriate status code
        """
        # Log the full traceback for debugging
        logger.error(f"Unexpected error: {str(exc)}")
        logger.error(f"Request path: {request.url.path}")
        logger.error(traceback.format_exc())
        
        # Log request information for debugging
        logger.error(f"Request method: {request.method}")
        logger.error(f"Request headers: {request.headers}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=self._format_error_response(
                "An unexpected error occurred",
                "internal_server_error",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        )
    
    def _format_error_response(
        self, message: str, error_type: str, status_code: int
    ) -> Dict[str, Any]:
        """
        Format the error response.
        
        Args:
            message: Error message
            error_type: Type of error
            status_code: HTTP status code
            
        Returns:
            Dict: Formatted error response
        """
        return {
            "error": {
                "message": message,
                "type": error_type,
                "status_code": status_code
            }
        } 