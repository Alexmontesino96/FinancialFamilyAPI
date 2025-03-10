# API de Family Finance

## Introducción

La API de Family Finance es una solución completa para la gestión de finanzas compartidas entre miembros de una familia o grupo. Diseñada con FastAPI y PostgreSQL, esta API proporciona una interfaz robusta y eficiente para:

- **Gestión de grupos familiares**: Crear y administrar grupos familiares o de amigos que comparten gastos.
- **Registro de miembros**: Añadir miembros a los grupos y gestionar sus perfiles.
- **Control de gastos compartidos**: Registrar gastos y especificar cómo se dividen entre los miembros.
- **Seguimiento de pagos**: Registrar pagos entre miembros para saldar deudas.
- **Cálculo de balances**: Obtener en tiempo real el estado de cuentas de cada miembro, incluyendo deudas y créditos.
- **Autenticación segura**: Proteger los datos mediante autenticación basada en tokens JWT.

Esta API está diseñada para ser utilizada por aplicaciones cliente como bots de Telegram, aplicaciones web o móviles que necesiten una solución backend para la gestión de finanzas compartidas.

## Características principales

- **Arquitectura RESTful**: Endpoints bien definidos siguiendo las mejores prácticas de diseño de APIs.
- **Documentación interactiva**: Interfaz Swagger/OpenAPI para explorar y probar los endpoints.
- **Base de datos PostgreSQL**: Almacenamiento persistente y relacional para garantizar la integridad de los datos.
- **Seguridad**: Autenticación mediante tokens JWT y protección de endpoints sensibles.
- **Escalabilidad**: Diseñada para manejar múltiples familias y miembros de manera eficiente.

Esta API proporciona los servicios necesarios para gestionar las finanzas familiares, incluyendo la creación de familias, miembros, gastos y pagos.

## Requisitos

- Python 3.8+
- PostgreSQL

## Instalación

1. Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd <directorio-del-repositorio>/api
```

2. Crear un entorno virtual:

```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar las variables de entorno:

Crea un archivo `.env` en el directorio `api` con el siguiente contenido:

```
# Configuración de la base de datos
DATABASE_URL=postgresql://familyfinance:tu_contraseña_segura@localhost/familyfinance

# Configuración de seguridad
SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de la API
API_PORT=8007
API_HOST=0.0.0.0
```

5. Configurar PostgreSQL:

```bash
# Crear la base de datos
createdb familyfinance

# Crear un usuario específico para la aplicación
psql -U postgres -c "CREATE USER familyfinance WITH PASSWORD 'tu_contraseña_segura';"
psql -U postgres -c "ALTER USER familyfinance WITH SUPERUSER;"
```

## Ejecución

Para ejecutar la API:

```bash
python run.py
```

La API estará disponible en `http://localhost:8007`.

## Documentación

La documentación de la API estará disponible en `http://localhost:8007/docs`.

## Testing

La API incluye un conjunto completo de pruebas automatizadas para garantizar su correcto funcionamiento. Las pruebas están implementadas utilizando pytest y cubren los principales endpoints y funcionalidades.

### Requisitos para las pruebas

- pytest
- pytest-cov (para análisis de cobertura)
- httpx (requerido por TestClient de FastAPI)

Puedes instalar estas dependencias con:

```bash
pip install pytest pytest-cov httpx
```

### Ejecutar las pruebas

Para ejecutar todas las pruebas:

```bash
pytest
```

Para ejecutar las pruebas con información de cobertura:

```bash
pytest --cov=app
```

Para generar un informe HTML de cobertura:

```bash
pytest --cov=app --cov-report=html
```

El informe de cobertura estará disponible en el directorio `htmlcov`.

### Estructura de las pruebas

- `tests/conftest.py`: Configuración y fixtures para las pruebas
- `tests/test_auth.py`: Pruebas de autenticación
- `tests/test_families.py`: Pruebas de operaciones con familias
- `tests/test_expenses.py`: Pruebas de operaciones con gastos

### Estrategia de pruebas

Las pruebas utilizan una base de datos SQLite en memoria para aislar el entorno de pruebas del entorno de producción. Cada prueba se ejecuta en una transacción independiente que se revierte al finalizar, garantizando que las pruebas no interfieran entre sí.

## Endpoints

### Autenticación

- `POST /auth/token`: Obtiene un token de acceso.

### Familias

- `POST /families/`: Crea una nueva familia.
- `GET /families/{family_id}`: Obtiene información de una familia.
- `GET /families/{family_id}/members`: Obtiene los miembros de una familia.
- `POST /families/{family_id}/members`: Añade un miembro a una familia.
- `GET /families/{family_id}/balances`: Obtiene los balances de una familia.

### Miembros

- `GET /members/{telegram_id}`: Obtiene un miembro por su ID de Telegram.
- `GET /members/me`: Obtiene el miembro actual.
- `GET /members/me/balance`: Obtiene el balance del miembro actual.
- `PUT /members/{member_id}`: Actualiza un miembro.
- `DELETE /members/{member_id}`: Elimina un miembro.

### Gastos

- `POST /expenses/`: Crea un nuevo gasto.
- `GET /expenses/{expense_id}`: Obtiene un gasto por su ID.
- `GET /expenses/family/{family_id}`: Obtiene los gastos de una familia.
- `DELETE /expenses/{expense_id}`: Elimina un gasto.

### Pagos

- `POST /payments/`: Crea un nuevo pago.
- `GET /payments/{payment_id}`: Obtiene un pago por su ID.
- `GET /payments/family/{family_id}`: Obtiene los pagos de una familia.
- `DELETE /payments/{payment_id}`: Elimina un pago. 