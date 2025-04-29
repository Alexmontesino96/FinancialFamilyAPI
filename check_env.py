import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Mostrar ruta del archivo actual
print(f"Ruta actual: {os.path.abspath(__file__)}")

# Mostrar ruta de trabajo actual
print(f"Directorio de trabajo: {os.getcwd()}")

# Verificar si DATABASE_URL está en el entorno
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Ocultar contraseña para seguridad
    masked_url = database_url
    if "@" in database_url:
        parts = database_url.split("@")
        masked_url = parts[0].split(":")
        masked_url = f"{masked_url[0]}:****@{parts[1]}"
    print(f"DATABASE_URL está configurada: {masked_url}")
else:
    print("DATABASE_URL no está configurada")

# Mostrar otras variables de entorno relevantes
print("\nOtras variables de entorno:")
for env_var in ["SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES"]:
    value = os.getenv(env_var)
    if value:
        if env_var == "SECRET_KEY":
            print(f"{env_var}: ****")
        else:
            print(f"{env_var}: {value}")
    else:
        print(f"{env_var}: no configurada")

# Mostrar información sobre la búsqueda de .env
print("\nBúsqueda de archivo .env:")
if os.path.exists(".env"):
    print("Archivo .env encontrado en el directorio actual")
    with open(".env", "r") as f:
        print("Contenido (primeras líneas sin valores sensibles):")
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                if key in ["DATABASE_URL", "SECRET_KEY"]:
                    print(f"{key}=****")
                else:
                    print(f"{key}={value}")
else:
    print("No se encontró archivo .env en el directorio actual")

# Buscar .env en directorios padres
parent_dir = os.path.dirname(os.getcwd())
if os.path.exists(os.path.join(parent_dir, ".env")):
    print(f"Archivo .env encontrado en el directorio padre: {parent_dir}") 