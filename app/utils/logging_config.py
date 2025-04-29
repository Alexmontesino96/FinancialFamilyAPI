"""
Módulo de configuración de logging

Este módulo proporciona una configuración centralizada para el sistema de
logging de la aplicación, estableciendo formatos consistentes y niveles
apropiados para los diferentes entornos.
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Obtener directorio base de la aplicación
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Crear directorio de logs si no existe
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuración básica de logging
def setup_logging(level=logging.INFO):
    """
    Configura el sistema de logging con un formato y nivel específicos.
    
    Args:
        level: Nivel de logging (por defecto INFO)
    """
    # Obtener el logger raíz
    root_logger = logging.getLogger()
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Establecer nivel de logging
    root_logger.setLevel(level)
    
    # Crear formato para los logs
    log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configurar handler para archivo
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, f"app-{current_date}.log"),
        maxBytes=10485760,  # 10 MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Configurar loggers específicos de la aplicación
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    
    # Suprimir logs innecesarios de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    app_logger.info("Sistema de logging inicializado")

def get_logger(name):
    """
    Obtiene un logger con el nombre específico.
    
    Args:
        name: Nombre del módulo/componente para el logger
    
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(f"app.{name}") 