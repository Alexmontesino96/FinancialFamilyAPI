from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.models.database import engine, Base
from app.routers import families, members, expenses, payments, auth

# Cargar variables de entorno
load_dotenv()

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear la aplicación
app = FastAPI(
    title="Family Finance API",
    description="API para gestionar las finanzas familiares",
    version="1.0.0"
)

# Configurar CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(families.router)
app.include_router(members.router)
app.include_router(expenses.router)
app.include_router(payments.router)

@app.get("/")
def read_root():
    """Endpoint raíz de la API."""
    return {"message": "Bienvenido a la API de Family Finance"}

# Ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8007"))
    
    uvicorn.run("main:app", host=host, port=port, reload=True) 