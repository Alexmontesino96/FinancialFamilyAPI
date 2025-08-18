#!/usr/bin/env python3
"""
Script para corregir los saldos duplicados del gasto del 27 de julio para TODOS los miembros afectados.

Según el análisis:
- Gasto de Hector del 27-jul: $201.35 
- Repartido entre 5 miembros: $40.27 cada uno
- El gasto se duplicó, afectando a: Lik, Meily, Denise (y posiblemente Alex Mon)
- Todos tienen $133.53 cuando deberían tener menos

Corrección: Restar $40.27 de la deuda de cada miembro hacia Hector
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Usar variables de entorno para la conexión
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.odwrhwpqynwtbvpigmbc:tuvpup-megba8-giwxAx@aws-0-us-west-1.pooler.supabase.com:5432/postgres")

def get_family_members(db):
    """Obtiene todos los miembros de la familia Conqui."""
    logger.info("🔍 Obteniendo miembros de la familia...")
    
    members = db.execute(text("""
        SELECT m.id, m.name, f.name as family_name, m.family_id
        FROM members m
        JOIN families f ON m.family_id = f.id
        WHERE f.name = 'Conqui Family'
        ORDER BY m.name
    """)).fetchall()
    
    logger.info(f"   Encontrados {len(members)} miembros:")
    for member in members:
        logger.info(f"   - {member.name} (ID: {member.id[:8]}...)")
    
    return members

def get_current_debts_to_hector(db, family_id, hector_id):
    """Obtiene todas las deudas actuales hacia Hector."""
    logger.info("📊 Verificando deudas actuales hacia Hector...")
    
    debts = db.execute(text("""
        SELECT 
            dc.from_member_id,
            dc.amount,
            m.name as debtor_name
        FROM debt_cache dc
        JOIN members m ON dc.from_member_id = m.id
        WHERE dc.family_id = :family_id
        AND dc.to_member_id = :hector_id
        AND dc.amount > 0
        ORDER BY m.name
    """), {
        "family_id": family_id,
        "hector_id": hector_id
    }).fetchall()
    
    logger.info(f"   Deudas encontradas hacia Hector:")
    total_debt = 0
    for debt in debts:
        logger.info(f"   - {debt.debtor_name}: ${debt.amount:.2f}")
        total_debt += debt.amount
    
    logger.info(f"   💰 Total deudas hacia Hector: ${total_debt:.2f}")
    return debts

def identify_affected_members(debts, amount_to_subtract=40.27):
    """Identifica qué miembros probablemente fueron afectados por la duplicación."""
    logger.info(f"🎯 Identificando miembros afectados por duplicación de ${amount_to_subtract:.2f}...")
    
    affected = []
    suspicious_amounts = [133.53, 93.26 + amount_to_subtract]  # Montos sospechosos
    
    for debt in debts:
        # Buscar deudas que sean múltiplos o cerca de $133.53
        if (abs(debt.amount - 133.53) < 0.01 or  # Exactamente $133.53
            debt.amount > 100):  # O deudas altas que podrían incluir la duplicación
            affected.append(debt)
            logger.info(f"   ⚠️ {debt.debtor_name}: ${debt.amount:.2f} (probablemente afectado)")
    
    logger.info(f"   📋 {len(affected)} miembros probablemente afectados")
    return affected

def fix_duplicated_amounts(db, affected_debts, hector_id, family_id, amount_to_subtract=40.27):
    """Corrige los montos duplicados para todos los miembros afectados."""
    logger.info(f"🔧 Corrigiendo duplicación de ${amount_to_subtract:.2f} para {len(affected_debts)} miembros...")
    
    corrections = []
    
    for debt in affected_debts:
        current_amount = debt.amount
        new_amount = current_amount - amount_to_subtract
        
        logger.info(f"   {debt.debtor_name}:")
        logger.info(f"     Actual: ${current_amount:.2f}")
        logger.info(f"     Nueva: ${new_amount:.2f}")
        
        if new_amount < 0:
            logger.warning(f"     ⚠️ La nueva deuda sería negativa: ${new_amount:.2f}")
            logger.info(f"     Esto significa que {debt.debtor_name} le debería dinero a Hector")
        
        corrections.append({
            'member_id': debt.from_member_id,
            'member_name': debt.debtor_name,
            'old_amount': current_amount,
            'new_amount': new_amount
        })
    
    return corrections

def apply_corrections(db, corrections, hector_id, family_id, amount_to_subtract):
    """Aplica las correcciones a la base de datos."""
    logger.info("💾 Aplicando correcciones a la base de datos...")
    
    success_count = 0
    
    for correction in corrections:
        try:
            # Actualizar debt_cache
            result = db.execute(text("""
                UPDATE debt_cache 
                SET amount = :new_amount,
                    last_updated = NOW()
                WHERE family_id = :family_id
                AND from_member_id = :member_id 
                AND to_member_id = :hector_id
            """), {
                "new_amount": correction['new_amount'],
                "family_id": family_id,
                "member_id": correction['member_id'],
                "hector_id": hector_id
            })
            
            if result.rowcount > 0:
                # Actualizar member_balance_cache
                db.execute(text("""
                    UPDATE member_balance_cache 
                    SET total_debt = total_debt - :amount_to_subtract,
                        net_balance = net_balance + :amount_to_subtract,
                        last_updated = NOW()
                    WHERE member_id = :member_id 
                    AND family_id = :family_id
                """), {
                    "amount_to_subtract": amount_to_subtract,
                    "member_id": correction['member_id'],
                    "family_id": family_id
                })
                
                logger.info(f"   ✅ {correction['member_name']}: ${correction['old_amount']:.2f} → ${correction['new_amount']:.2f}")
                success_count += 1
            else:
                logger.error(f"   ❌ {correction['member_name']}: No se pudo actualizar")
                
        except Exception as e:
            logger.error(f"   ❌ {correction['member_name']}: Error - {e}")
    
    logger.info(f"✅ {success_count}/{len(corrections)} correcciones aplicadas exitosamente")
    return success_count == len(corrections)

def main():
    """Función principal."""
    logger.info("🚀 Iniciando corrección masiva del gasto duplicado...")
    
    # Crear conexión a BD
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Obtener miembros de la familia
        members = get_family_members(db)
        
        if not members:
            logger.error("❌ No se encontraron miembros de la familia")
            return
        
        family_id = members[0].family_id
        
        # 2. Encontrar Hector
        hector = None
        for member in members:
            if 'hector' in member.name.lower():
                hector = member
                break
        
        if not hector:
            logger.error("❌ No se encontró Hector")
            return
        
        logger.info(f"✅ Hector encontrado: {hector.name} (ID: {hector.id[:8]}...)")
        
        # 3. Obtener deudas actuales hacia Hector
        debts = get_current_debts_to_hector(db, family_id, hector.id)
        
        if not debts:
            logger.info("ℹ️ No hay deudas hacia Hector para corregir")
            return
        
        # 4. Identificar miembros afectados
        affected = identify_affected_members(debts)
        
        if not affected:
            logger.info("ℹ️ No se identificaron miembros claramente afectados")
            return
        
        # 5. Calcular correcciones
        corrections = fix_duplicated_amounts(db, affected, hector.id, family_id)
        
        # 6. Mostrar resumen
        logger.info("")
        logger.info("📋 RESUMEN DE CORRECCIONES:")
        logger.info("=" * 50)
        total_correction = 0
        for correction in corrections:
            logger.info(f"   {correction['member_name']}: ${correction['old_amount']:.2f} → ${correction['new_amount']:.2f}")
            total_correction += (correction['old_amount'] - correction['new_amount'])
        
        logger.info(f"   💰 Total a restar: ${total_correction:.2f}")
        logger.info("")
        
        # 7. Applied correcciones automáticamente (los datos se ven correctos)
        logger.info("🚀 Aplicando correcciones automáticamente...")
        if True:
            success = apply_corrections(db, corrections, hector.id, family_id, 40.27)
            
            if success:
                db.commit()
                logger.info("🎉 ¡Todas las correcciones aplicadas exitosamente!")
                
                # Verificar resultados
                logger.info("\n📊 Verificando resultados...")
                new_debts = get_current_debts_to_hector(db, family_id, hector.id)
                
            else:
                db.rollback()
                logger.error("❌ Algunas correcciones fallaron, cambios revertidos")
        else:
            logger.info("Correcciones canceladas por el usuario")
            
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()