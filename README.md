# FinancialFamilyAPI

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-CC2927?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Una API robusta para la gestión de finanzas compartidas entre miembros de una familia o grupo de amigos.

## 📋 Descripción

FinancialFamilyAPI es una solución completa para la gestión de finanzas compartidas, diseñada para simplificar el seguimiento de gastos y deudas entre miembros de un grupo. La API proporciona:

- **Gestión de grupos familiares**: Creación y administración de grupos que comparten gastos.
- **Registro de miembros**: Gestión de perfiles de usuarios dentro de cada grupo.
- **Control de gastos compartidos**: Registro de gastos con división personalizada entre miembros.
- **Seguimiento de pagos**: Registro de transacciones entre miembros para saldar deudas.
- **Cálculo de balances**: Generación en tiempo real del estado de cuentas de cada miembro.

## 🚀 Tecnologías

- **FastAPI**: Framework web de alto rendimiento con validación automática
- **PostgreSQL**: Base de datos relacional para almacenamiento persistente
- **SQLAlchemy**: ORM para interacción con la base de datos
- **Pydantic**: Validación de datos y serialización
- **JWT**: Autenticación segura mediante tokens
- **Pytest**: Framework para pruebas automatizadas

## ⚙️ Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Alexmontesino96/FinancialFamilyAPI.git
cd FinancialFamilyAPI

# Crear entorno virtual
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos PostgreSQL
# Ver instrucciones detalladas en la sección de configuración
```

## 🔧 Configuración

1. Crea un archivo `.env` en el directorio raíz con el siguiente contenido:

```
# Configuración de la base de datos
DATABASE_URL=postgresql://usuario:contraseña@localhost/familyfinance

# Configuración de seguridad
SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de la API
API_PORT=8007
API_HOST=0.0.0.0
```

2. Configura PostgreSQL:

```bash
# Crear la base de datos
createdb familyfinance

# Crear un usuario específico para la aplicación
psql -U postgres -c "CREATE USER familyfinance WITH PASSWORD 'tu_contraseña_segura';"
psql -U postgres -c "ALTER USER familyfinance WITH SUPERUSER;"
```

## 🏃‍♂️ Ejecución

```bash
# Iniciar la API
python -m app.main

# La API estará disponible en http://localhost:8007
# La documentación interactiva estará en http://localhost:8007/docs
```

## 🧪 Pruebas

El proyecto incluye pruebas automatizadas para garantizar su correcto funcionamiento:

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con información de cobertura
pytest --cov=app

# Generar informe HTML de cobertura
pytest --cov=app --cov-report=html
```

## 📚 Documentación

La documentación completa de la API está disponible en:

- **Swagger UI**: http://localhost:8007/docs
- **ReDoc**: http://localhost:8007/redoc

Para información técnica más detallada, consulte el archivo [README_ORIGINAL.md](README_ORIGINAL.md).

## 👨‍💻 Autor

**Alex Montesino** - [@Alexmontesino96](https://github.com/Alexmontesino96)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

- Abre un [issue](https://github.com/Alexmontesino96/FinancialFamilyAPI/issues) en este repositorio
- Contacta directamente a través de GitHub: [@Alexmontesino96](https://github.com/Alexmontesino96) 