import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_db
from app.models.models import Family, Member, Expense, Payment

# Crear una base de datos en memoria para las pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    # Crear las tablas en la base de datos de prueba
    Base.metadata.create_all(bind=engine)
    
    # Crear una sesión de prueba
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Limpiar la base de datos después de cada prueba
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    # Sobreescribir la dependencia get_db para usar la base de datos de prueba
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Restaurar la dependencia original
    app.dependency_overrides = {} 