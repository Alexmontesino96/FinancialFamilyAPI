# FinancialFamilyAPI

API para la gestión de finanzas compartidas entre miembros de una familia o grupo.

## Descripción

FinancialFamilyAPI es una solución completa para la gestión de finanzas compartidas. Diseñada con FastAPI y PostgreSQL, esta API proporciona una interfaz robusta y eficiente para:

- **Gestión de grupos familiares**: Crear y administrar grupos familiares o de amigos que comparten gastos.
- **Registro de miembros**: Añadir miembros a los grupos y gestionar sus perfiles.
- **Control de gastos compartidos**: Registrar gastos y especificar cómo se dividen entre los miembros.
- **Seguimiento de pagos**: Registrar pagos entre miembros para saldar deudas.
- **Cálculo de balances**: Obtener en tiempo real el estado de cuentas de cada miembro.

## Tecnologías

- **FastAPI**: Framework web moderno y de alto rendimiento
- **PostgreSQL**: Base de datos relacional robusta
- **SQLAlchemy**: ORM para interactuar con la base de datos
- **Pydantic**: Validación de datos y serialización
- **JWT**: Autenticación segura mediante tokens
- **Pytest**: Framework de pruebas automatizadas

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/USERNAME/FinancialFamilyAPI.git
cd FinancialFamilyAPI

# Crear entorno virtual
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
# Ver instrucciones detalladas en README.md
```

## Documentación

La documentación completa está disponible en el archivo [README.md](README.md).

## Pruebas

El proyecto incluye pruebas automatizadas para garantizar su correcto funcionamiento:

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas con información de cobertura
pytest --cov=app
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Para cualquier consulta o sugerencia, por favor abre un issue en este repositorio. 