# Documentación Técnica - FinancialFamilyAPI

Esta documentación técnica proporciona información detallada sobre la implementación, configuración y uso de FinancialFamilyAPI.

## Arquitectura

FinancialFamilyAPI está construida siguiendo una arquitectura de capas:

1. **Capa de API**: Implementada con FastAPI, maneja las solicitudes HTTP y respuestas.
2. **Capa de Servicios**: Contiene la lógica de negocio principal.
3. **Capa de Modelos**: Define las entidades de datos y su representación en la base de datos.
4. **Capa de Persistencia**: Gestiona la interacción con PostgreSQL mediante SQLAlchemy.

## Estructura del Proyecto

```
api/
├── app/
│   ├── auth/              # Autenticación y seguridad
│   ├── models/            # Modelos de datos y esquemas
│   ├── routers/           # Endpoints de la API
│   ├── services/          # Lógica de negocio
│   └── main.py            # Punto de entrada de la aplicación
├── tests/                 # Pruebas automatizadas
├── .env                   # Variables de entorno
├── requirements.txt       # Dependencias
└── README.md              # Documentación
```

## Requisitos del Sistema

- Python 3.8+
- PostgreSQL 12+
- Dependencias listadas en `requirements.txt`

## Configuración Detallada

### Variables de Entorno

Crea un archivo `.env` en el directorio raíz con las siguientes variables:

```
# Base de datos
DATABASE_URL=postgresql://familyfinance:tu_contraseña_segura@localhost/familyfinance

# Seguridad
SECRET_KEY=tu_clave_secreta_de_al_menos_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_PORT=8007
API_HOST=0.0.0.0
```

### Configuración de PostgreSQL

1. Instala PostgreSQL si aún no lo tienes:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS con Homebrew
   brew install postgresql
   ```

2. Inicia el servicio de PostgreSQL:
   ```bash
   # Ubuntu/Debian
   sudo service postgresql start
   
   # macOS
   brew services start postgresql
   ```

3. Crea la base de datos y el usuario:
   ```bash
   # Crear la base de datos
   createdb familyfinance
   
   # Crear un usuario específico para la aplicación
   psql -U postgres -c "CREATE USER familyfinance WITH PASSWORD 'tu_contraseña_segura';"
   psql -U postgres -c "ALTER USER familyfinance WITH SUPERUSER;"
   ```

## Instalación Paso a Paso

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Alexmontesino96/FinancialFamilyAPI.git
   cd FinancialFamilyAPI
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno como se describió anteriormente.

5. Ejecuta la aplicación:
   ```bash
   python -m app.main
   ```

## Pruebas Automatizadas

### Configuración de Pruebas

Las pruebas utilizan una base de datos SQLite en memoria para aislar el entorno de pruebas. La configuración se encuentra en `tests/conftest.py`.

### Ejecución de Pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con información de cobertura
pytest --cov=app

# Generar informe HTML de cobertura
pytest --cov=app --cov-report=html
```

### Estructura de las Pruebas

- `tests/conftest.py`: Configuración y fixtures para las pruebas
- `tests/test_auth.py`: Pruebas de autenticación
- `tests/test_families.py`: Pruebas de operaciones con familias
- `tests/test_expenses.py`: Pruebas de operaciones con gastos

## Referencia de API

### Autenticación

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/auth/token` | POST | Obtiene un token de acceso | `username`: ID de Telegram del usuario |

### Familias

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/families/` | POST | Crea una nueva familia | `name`: Nombre de la familia, `members`: Lista de miembros |
| `/families/{family_id}` | GET | Obtiene información de una familia | `family_id`: ID de la familia |
| `/families/{family_id}/members` | GET | Obtiene los miembros de una familia | `family_id`: ID de la familia |
| `/families/{family_id}/members` | POST | Añade un miembro a una familia | `family_id`: ID de la familia, `member`: Datos del miembro |
| `/families/{family_id}/balances` | GET | Obtiene los balances de una familia | `family_id`: ID de la familia |

### Miembros

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/members/{telegram_id}` | GET | Obtiene un miembro por su ID de Telegram | `telegram_id`: ID de Telegram |
| `/members/me` | GET | Obtiene el miembro actual | Requiere token de autenticación |
| `/members/me/balance` | GET | Obtiene el balance del miembro actual | Requiere token de autenticación |
| `/members/{member_id}` | PUT | Actualiza un miembro | `member_id`: ID del miembro, `member`: Datos actualizados |
| `/members/{member_id}` | DELETE | Elimina un miembro | `member_id`: ID del miembro |

### Gastos

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/expenses/` | POST | Crea un nuevo gasto | `description`, `amount`, `paid_by`, `split_among` |
| `/expenses/{expense_id}` | GET | Obtiene un gasto por su ID | `expense_id`: ID del gasto |
| `/expenses/family/{family_id}` | GET | Obtiene los gastos de una familia | `family_id`: ID de la familia |
| `/expenses/{expense_id}` | DELETE | Elimina un gasto | `expense_id`: ID del gasto |

### Pagos

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/payments/` | POST | Crea un nuevo pago | `from_member`, `to_member`, `amount` |
| `/payments/{payment_id}` | GET | Obtiene un pago por su ID | `payment_id`: ID del pago |
| `/payments/family/{family_id}` | GET | Obtiene los pagos de una familia | `family_id`: ID de la familia |
| `/payments/{payment_id}` | DELETE | Elimina un pago | `payment_id`: ID del pago |

## Modelos de Datos

### Family
- `id`: String (UUID)
- `name`: String
- `created_at`: DateTime
- `members`: Relación con Member

### Member
- `id`: Integer
- `name`: String
- `telegram_id`: String
- `family_id`: String (UUID)
- `created_at`: DateTime

### Expense
- `id`: String (UUID)
- `description`: String
- `amount`: Float
- `paid_by`: Integer (ID de Member)
- `family_id`: String (UUID)
- `created_at`: DateTime
- `split_among`: Relación con Member

### Payment
- `id`: String (UUID)
- `from_member_id`: Integer (ID de Member)
- `to_member_id`: Integer (ID de Member)
- `amount`: Float
- `family_id`: String (UUID)
- `created_at`: DateTime

## Seguridad

La API utiliza autenticación basada en tokens JWT. Cada solicitud a un endpoint protegido debe incluir un token válido en el encabezado de autorización:

```
Authorization: Bearer {token}
```

Los tokens se obtienen mediante el endpoint `/auth/token` proporcionando el ID de Telegram del usuario. 