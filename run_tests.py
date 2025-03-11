#!/usr/bin/env python
"""
Script para ejecutar pruebas en el proyecto FinancialFamilyAPI.

Ejemplos de uso:
    # Ejecutar todas las pruebas
    python run_tests.py
    
    # Ejecutar pruebas con cobertura
    python run_tests.py --cov
    
    # Ejecutar solo pruebas de servicios
    python run_tests.py --services
    
    # Ejecutar pruebas de un servicio específico
    python run_tests.py --service=balance
"""

import argparse
import os
import sys
import subprocess

def run_tests(args):
    """
    Ejecuta las pruebas según los argumentos proporcionados.
    
    Args:
        args: Argumentos de línea de comandos analizados
    """
    cmd = ["pytest"]
    
    # Configurar la verbosidad
    if args.verbose:
        cmd.append("-v")
    
    # Añadir cobertura si se solicita
    if args.cov:
        cmd.extend(["--cov=app", "--cov-report=term"])
        
        # Generar informe HTML si se solicita
        if args.html:
            cmd.append("--cov-report=html")
    
    # Filtrar por tipo de prueba
    if args.services:
        cmd.append("tests/services/")
    
    # Filtrar por servicio específico
    if args.service:
        service_name = args.service.lower()
        cmd.append(f"tests/services/test_{service_name}_service.py")
    
    # Ejecutar el comando
    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode

def main():
    """
    Función principal que analiza los argumentos y ejecuta las pruebas.
    """
    parser = argparse.ArgumentParser(description="Ejecuta pruebas para FinancialFamilyAPI")
    
    # Opciones generales
    parser.add_argument("-v", "--verbose", action="store_true", help="Muestra salida detallada")
    
    # Opciones de cobertura
    parser.add_argument("--cov", action="store_true", help="Genera informe de cobertura")
    parser.add_argument("--html", action="store_true", help="Genera informe de cobertura en HTML")
    
    # Filtros por tipo de prueba
    parser.add_argument("--services", action="store_true", help="Ejecuta pruebas de servicios")
    parser.add_argument("--service", type=str, help="Ejecuta pruebas de un servicio específico (ej: balance, member, etc.)")
    
    args = parser.parse_args()
    
    # Ejecutar las pruebas
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main()) 