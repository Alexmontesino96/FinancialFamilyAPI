#!/usr/bin/env python
"""
Script para ejecutar pruebas de servicios sin depender de la configuración global.

Este script ejecuta las pruebas independientemente, evitando la carga de conftest.py
que podría requerir conexión a bases de datos externas.
"""

import unittest
import sys
import os
from unittest import mock

# Añadir el directorio raíz al PATH para que las importaciones funcionen
sys.path.insert(0, os.path.abspath('.'))

# Mockear las dependencias problemáticas
mock.patch('app.models.database.get_db').start()

# Importar y ejecutar las pruebas de balance
from tests.services.test_balance_service import TestBalanceService

# Crear un runner de tests
runner = unittest.TextTestRunner(verbosity=2)
suite = unittest.TestLoader().loadTestsFromTestCase(TestBalanceService)

# Ejecutar las pruebas
result = runner.run(suite)

# Importar y ejecutar las pruebas de miembros
from tests.services.test_member_service import TestMemberService
suite = unittest.TestLoader().loadTestsFromTestCase(TestMemberService)
result = runner.run(suite)

# Devolver el código de salida adecuado
sys.exit(not result.wasSuccessful()) 