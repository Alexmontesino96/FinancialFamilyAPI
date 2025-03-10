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
import os
from dotenv import load_dotenv

from app.models.database import engine, Base
from app.routers import families, members, expenses, payments, auth

# Load environment variables from .env file
load_dotenv()

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

@app.get("/")
def read_root():
    """
    Root endpoint of the API.
    
    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to the Family Finance API"}

# Run the application when executed directly
if __name__ == "__main__":
    import uvicorn
    
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8007"))
    
    # Start the uvicorn server with hot-reload enabled for development
    uvicorn.run("main:app", host=host, port=port, reload=True) 