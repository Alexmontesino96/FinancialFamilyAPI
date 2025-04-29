"""
Token Service para Bot de Telegram

Este módulo proporciona funciones para gestionar tokens basados en el ID de Telegram.
Para simplificar la integración con el bot, usamos directamente el ID de Telegram como token.
"""

from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Crea un token basado en el ID de Telegram.
    
    Para simplificar la integración con el bot de Telegram,
    esta implementación simplemente devuelve el ID de Telegram como token.
    
    Args:
        data: Diccionario con los datos del usuario (debe incluir 'sub' con el telegram_id)
        expires_delta: Tiempo opcional de expiración (no usado en esta implementación)
        
    Returns:
        str: Token (ID de Telegram)
    """
    # Obtenemos el ID de Telegram
    telegram_id = data.get("sub", "")
    if not telegram_id:
        raise ValueError("Se requiere el ID de Telegram en el campo 'sub'")
    
    # Usar directamente el ID como token
    return telegram_id 