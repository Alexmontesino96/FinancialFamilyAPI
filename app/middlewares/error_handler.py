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
from typing import Dict, Any, Union, Callable
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clase alternativa para compatibilidad con Starlette
class ErrorHandler:
    """
    Clase para compatibilidad con Starlette.
    Esta clase es necesaria porque Starlette busca una clase llamada ErrorHandler.
    """
    def __init__(self, app=None):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

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
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            Response: Either the normal response or an error response
        """
        try:
            # Intentar procesar la solicitud normalmente
            response = await call_next(request)
            return response
        except SQLAlchemyError as e:
            # Database errors
            logger.error(f"Database error: {str(e)}")
            logger.error(f"Request path: {request.url.path}")
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=self._format_error_response(
                    "Database error occurred",
                    "database_error",
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )
        except ValueError as e:
            # Value errors (validation, etc.)
            logger.warning(f"Value error: {str(e)}")
            logger.warning(f"Request path: {request.url.path}")
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=self._format_error_response(
                    str(e),
                    "value_error",
                    status.HTTP_400_BAD_REQUEST
                )
            )
        except Exception as e:
            # Unexpected errors (including custom exceptions)
            try:
                # Intentar registrar información detallada del error
                error_message = str(e)
                error_type = type(e).__name__
                logger.error(f"Unexpected error: {error_message}")
                logger.error(f"Error type: {error_type}")
                logger.error(f"Request path: {request.url.path}")
                
                # Registrar el traceback completo si estamos en modo debug
                # o si no es un error personalizado conocido
                if not hasattr(e, 'is_handled') or not e.is_handled:
                    logger.error(traceback.format_exc())
                
                # Registrar información de la solicitud para depuración
                logger.error(f"Request method: {request.method}")
                logger.error(f"Request headers: {request.headers}")
                
                # Intentar registrar información adicional si está disponible
                try:
                    if hasattr(request, 'query_params'):
                        logger.error(f"Query params: {request.query_params}")
                    
                    if hasattr(request, 'path_params'):
                        logger.error(f"Path params: {request.path_params}")
                        
                    # Intentar registrar atributos adicionales del error personalizado
                    if hasattr(e, '__dict__'):
                        safe_attrs = {}
                        for key, value in e.__dict__.items():
                            if key not in ('message', 'args') and not key.startswith('_'):
                                try:
                                    # Intentar serializar el valor o proporcionar una descripción segura
                                    if callable(value):
                                        safe_attrs[key] = "<<función no serializable>>"
                                    elif hasattr(value, '__dict__'):
                                        safe_attrs[key] = f"<<objeto {type(value).__name__}>>"
                                    else:
                                        safe_attrs[key] = str(value)
                                except Exception:
                                    safe_attrs[key] = "<<valor no serializable>>"
                        
                        if safe_attrs:
                            logger.error(f"Custom error attributes: {safe_attrs}")
                except Exception as log_err:
                    logger.error(f"Error logging request details: {str(log_err)}")
                
            except Exception as log_err:
                # Si hay un error al registrar el error, registrar esto también
                logger.error(f"Error logging exception: {str(log_err)}")
            
            # Siempre retornar una respuesta JSON válida
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