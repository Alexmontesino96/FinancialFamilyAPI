#!/usr/bin/env python3
"""
Script para ejecutar la API con los cambios de UUIDs.
"""

import os
import sys
import uvicorn

# Añadir el directorio de la aplicación al path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

if __name__ == "__main__":
    print("Iniciando la API...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8073, reload=True)
    print("API detenida.")  