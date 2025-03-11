#!/usr/bin/env python
"""
Script para ejecutar todas las pruebas aisladas de servicios.

Este script ejecuta las pruebas que no dependen de la base de datos
real, utilizando mocks para simular el comportamiento de la base de datos.
"""

import unittest
import sys
import os
import importlib
import glob

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath('.'))

def discover_and_run_tests():
    """
    Descubre y ejecuta todas las pruebas aisladas en el directorio tests/services/.
    
    Returns:
        bool: True si todas las pruebas pasan, False en caso contrario
    """
    # Encontrar todos los archivos de prueba con el prefijo test_isolated_
    test_files = glob.glob('tests/services/test_isolated_*.py')
    
    # Crear un suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir las pruebas de cada archivo al suite
    for test_file in test_files:
        # Convertir la ruta del archivo a un módulo importable
        module_path = test_file.replace('/', '.').replace('.py', '')
        print(f"Importando pruebas desde: {module_path}")
        
        try:
            # Importar el módulo
            module = importlib.import_module(module_path)
            
            # Añadir todas las clases de prueba del módulo
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                    print(f"  - Añadiendo clase de prueba: {name}")
                    suite.addTest(loader.loadTestsFromTestCase(obj))
        except Exception as e:
            print(f"Error al cargar el módulo {module_path}: {e}")
    
    # Ejecutar las pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Ejecutando pruebas aisladas de servicios...")
    success = discover_and_run_tests()
    
    # Devolver el código de salida adecuado
    sys.exit(0 if success else 1) 