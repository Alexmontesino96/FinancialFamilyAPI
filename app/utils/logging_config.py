"""
Logging Configuration Module

This module defines the configuration for the application's logging system.
It provides a consistent logging setup that can be used across the application.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# Configuración base para todos los loggers
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Directorio para los archivos de log
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name):
    """
    Get a configured logger with the specified name.
    
    Args:
        name (str): Name for the logger, typically __name__
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Evitar agregar múltiples handlers si el logger ya está configurado
    if logger.handlers:
        return logger
    
    logger.setLevel(LOG_LEVEL)
    
    # Configurar el formato para todos los handlers
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo
    # Cada módulo tiene su propio archivo de log
    module_name = name.split('.')[-1]
    file_handler = RotatingFileHandler(
        f"{LOG_DIR}/{module_name}.log", 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Evitar propagar logs al logger raíz para prevenir duplicados
    logger.propagate = False
    
    return logger 