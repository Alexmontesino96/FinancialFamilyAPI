"""
Script para inicializar el caché de balances para todas las familias existentes.

Este script utiliza el sistema de caché de balances implementado en BalanceService
para inicializar el caché de todas las familias existentes en la base de datos.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.models.database import SessionLocal
from app.models.models import Family
from app.services.balance_service import BalanceService
from app.utils.logging_config import get_logger

# Configurar logger
logger = get_logger("initialize_balance_cache")

def initialize_all_families_cache():
    """
    Inicializa el caché de balances para todas las familias existentes en la base de datos.
    """
    logger.info("Iniciando inicialización de caché para todas las familias")
    
    db = SessionLocal()
    try:
        # Obtener todas las familias
        families = db.query(Family).all()
        
        if not families:
            logger.info("No se encontraron familias en la base de datos.")
            return
        
        logger.info(f"Se encontraron {len(families)} familias para inicializar")
        
        # Inicializar el caché para cada familia
        for i, family in enumerate(families):
            try:
                logger.info(f"[{i+1}/{len(families)}] Inicializando caché para familia: {family.name} (ID: {family.id})")
                BalanceService.initialize_balance_cache(db, family.id)
                logger.info(f"✓ Caché inicializado exitosamente para familia: {family.name}")
            except Exception as e:
                logger.error(f"✗ Error al inicializar caché para familia {family.name}: {str(e)}")
        
        logger.info("Inicialización de caché completada")
        
    except Exception as e:
        logger.error(f"Error durante la inicialización del caché: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_all_families_cache()
