"""
Script para probar el sistema de logging

Este script prueba que el sistema de logging está configurado correctamente
generando logs de diferentes niveles y desde diferentes partes de la aplicación.
"""

import os
import sys
import logging
from app.utils.logging_config import setup_logging, get_logger

def test_logging():
    """Prueba que el sistema de logging funciona correctamente."""
    
    # Configurar el sistema de logging
    print("Configurando sistema de logging...")
    setup_logging(level=logging.DEBUG)
    
    # Obtener loggers para diferentes partes de la aplicación
    main_logger = get_logger("main")
    payment_logger = get_logger("payment_service")
    family_logger = get_logger("family_service")
    balance_logger = get_logger("balance_service")
    
    # Mostrar la ruta de los logs
    from app.utils.logging_config import LOGS_DIR
    print(f"Los archivos de log se guardarán en: {LOGS_DIR}")
    
    # Generar algunos logs de prueba
    print("\nGenerando logs de prueba...")
    
    main_logger.debug("Este es un log de depuración desde el módulo principal")
    main_logger.info("Este es un log informativo desde el módulo principal")
    main_logger.warning("Este es un log de advertencia desde el módulo principal")
    main_logger.error("Este es un log de error desde el módulo principal")
    
    payment_logger.info("Procesando pago de prueba")
    payment_logger.debug("Detalles del pago: monto=100.0, de=usuario1, para=usuario2")
    
    family_logger.info("Creando familia de prueba")
    family_logger.debug("Detalles de la familia: nombre=Familia de Prueba, miembros=3")
    
    balance_logger.info("Calculando balances para la familia de prueba")
    balance_logger.debug("Procesando 5 gastos y 2 pagos")
    
    # Simular un error
    try:
        # Provocar un error dividiendo por cero
        result = 1 / 0
    except Exception as e:
        main_logger.exception("Se ha producido un error inesperado")
    
    print("\nLogs generados correctamente. Verificar los archivos en el directorio de logs.")
    
    # Mostrar primeras 10 líneas del archivo de log más reciente
    log_files = [f for f in os.listdir(LOGS_DIR) if f.startswith("app-") and f.endswith(".log")]
    if log_files:
        newest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(LOGS_DIR, x)))
        log_path = os.path.join(LOGS_DIR, newest_log)
        print(f"\nMostrando las primeras 10 líneas del archivo de log más reciente: {newest_log}")
        try:
            with open(log_path, "r") as f:
                for i, line in enumerate(f):
                    if i < 10:
                        print(f"  {line.strip()}")
                    else:
                        break
                print("  ...")
        except Exception as e:
            print(f"Error al leer el archivo de log: {str(e)}")

if __name__ == "__main__":
    test_logging() 