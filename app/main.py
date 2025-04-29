"""
FinancialFamilyAPI - Main Application Module

This module initializes the FastAPI application, configures middleware,
registers routers, and sets up the database connection.

The API provides endpoints for managing family finances, including:
- Family and member management
- Expense tracking and splitting
- Payment recording
- Balance calculation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import os
import logging
import traceback
from dotenv import load_dotenv

from app.models.database import engine, Base
from app.routers import families, members, expenses, payments, auth, test_errors
from app.middlewares.http_exception_handler import http_exception_handler, validation_exception_handler
from app.utils.logging_config import setup_logging, get_logger

# Configurar el sistema de logging centralizado
setup_logging(level=logging.INFO)
logger = get_logger("main")

# Load environment variables from .env file
load_dotenv()

# Determine if we're in debug mode
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Family Finance API",
    description="API for managing shared family finances",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Set debug mode
app.debug = DEBUG
logger.info(f"Application running in {'DEBUG' if DEBUG else 'PRODUCTION'} mode")

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error(f"Database error: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Database error occurred",
                "type": "database_error",
                "status_code": 500
            }
        }
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    logger.warning(f"Value error: {str(exc)}")
    logger.warning(f"Request path: {request.url.path}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": str(exc),
                "type": "value_error",
                "status_code": 400
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Manejador global de excepciones no capturadas.
    
    Este manejador captura cualquier excepción no manejada por otros manejadores
    específicos, registra información detallada para depuración y devuelve una
    respuesta JSON estructurada.
    
    Args:
        request: La solicitud HTTP que generó la excepción
        exc: La excepción que se produjo
        
    Returns:
        JSONResponse: Una respuesta JSON con información sobre el error
    """
    # Registrar información detallada del error
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(traceback.format_exc())
    
    # Registrar información de la solicitud para depuración
    logger.error(f"Request method: {request.method}")
    logger.error(f"Request headers: {request.headers}")
    
    # Registrar información adicional si está disponible
    if hasattr(request, 'query_params'):
        logger.error(f"Query params: {request.query_params}")
    
    if hasattr(request, 'path_params'):
        logger.error(f"Path params: {request.path_params}")
    
    try:
        # Intentar obtener el cuerpo de la solicitud si es posible
        body = await request.body()
        if body:
            logger.error(f"Request body: {body.decode('utf-8', errors='replace')}")
    except Exception as body_err:
        logger.error(f"Could not read request body: {str(body_err)}")
    
    # Devolver una respuesta JSON estructurada
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "An unexpected error occurred",
                "type": "internal_server_error",
                "status_code": 500,
                "error_details": str(exc) if app.debug else None
            }
        }
    )

# Configure Cross-Origin Resource Sharing (CORS)
# This allows the API to be accessed from different domains/origins
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "*"  # Allow all origins in development (restrict in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Register API routers for different resource endpoints
app.include_router(auth.router)
app.include_router(families.router)
app.include_router(members.router)
app.include_router(expenses.router)
app.include_router(payments.router)
app.include_router(test_errors.router)

@app.get("/")
def read_root():
    """
    Root endpoint of the API.
    
    Returns:
        dict: A welcome message
    """
    logger.debug("Root endpoint accessed")
    return {"message": "Welcome to the Family Finance API"}

# Run the application when executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8007"))
    
    # Start the uvicorn server with hot-reload enabled for development
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) 