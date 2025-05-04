from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.models import Family, Member, Expense, Payment, PaymentStatus, PaymentType, MemberBalanceCache, DebtCache
from app.models.schemas import MemberBalance, DebtDetail, CreditDetail
from typing import List, Dict, Set, Tuple
from app.utils.logging_config import get_logger

# Configurar logging centralizado
logger = get_logger("balance_service")

class BalanceService:
    """
    Service for calculating family balances.
    
    This class provides methods for calculating the financial balances of family members,
    taking into account expenses and payments. Includes methods for caching balances
    and updating them incrementally for improved performance.
    """
    
    @staticmethod
    def calculate_family_balances(db: Session, family_id: str, debug_mode: bool = False) -> List[MemberBalance]:
        """
        Calculate the balances of all members in a family.
        
        This method calculates how much each member owes or is owed by other members,
        based on expenses and payments.
        
        Args:
            db: Database session
            family_id: ID of the family to calculate balances for
            debug_mode: If True, output detailed logs of the calculation process
            
        Returns:
            List[MemberBalance]: List of member balances with detailed debt and credit information
        """
        # Get all family members
        members = db.query(Member).filter(Member.family_id == family_id).all()
        member_ids = [m.id for m in members]
        
        if debug_mode:
            logger.info(f"Calculating balances for family {family_id} with {len(members)} members")
            logger.info(f"Member IDs: {member_ids}")
        
        # Create a dictionary of members by ID for easy lookup
        members_by_id = {str(m.id): m for m in members}
        
        # Initialize the balance dictionary with string keys
        balances: Dict[str, Dict] = {}
        for member in members:
            member_id = str(member.id)
            balances[member_id] = {
                "member_id": member_id,
                "name": member.name,
                "total_debt": 0.0,
                "total_owed": 0.0,
                "net_balance": 0.0,
                "debts_by_member": {},  # Dictionary to track debts by member
                "credits_by_member": {},  # Dictionary to track credits by member
                "debts": [],
                "credits": []
            }
            if debug_mode:
                logger.info(f"Initialized balance for {member.name} (ID: {member_id})")
        
        # Process expenses
        expenses = db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
        if debug_mode:
            logger.info(f"Found {len(expenses)} expenses to process")
        
        for expense in expenses:
            # Get the member who paid
            payer_id = str(expense.paid_by)
            
            # Get the members among whom the expense is split
            split_members = expense.split_among
            
            # If no specific members, split among all
            if not split_members:
                split_members = members
            
            # Calculate the amount per member
            amount_per_member = expense.amount / len(split_members)
            
            if debug_mode:
                payer_name = members_by_id[payer_id].name if payer_id in members_by_id else "Unknown"
                logger.info(f"Processing expense: {expense.description}, ${expense.amount:.2f}, paid by {payer_name}")
                logger.info(f"Split among {len(split_members)} members, ${amount_per_member:.2f} per member")
            
            # Update the balances
            for member in split_members:
                member_id = str(member.id)
                
                # If the member is the payer, they don't owe themselves
                if member_id == payer_id:
                    if debug_mode:
                        logger.info(f"  - {members_by_id[member_id].name} is the payer, skipping self-debt")
                    continue
                
                # Initialize the debt tracking for this pair if needed
                if payer_id not in balances[member_id]["debts_by_member"]:
                    balances[member_id]["debts_by_member"][payer_id] = 0.0
                
                if member_id not in balances[payer_id]["credits_by_member"]:
                    balances[payer_id]["credits_by_member"][member_id] = 0.0
                
                # Update the debt amount
                balances[member_id]["debts_by_member"][payer_id] += amount_per_member
                balances[payer_id]["credits_by_member"][member_id] += amount_per_member
                
                # Update totals
                balances[member_id]["total_debt"] += amount_per_member
                balances[payer_id]["total_owed"] += amount_per_member
                
                if debug_mode:
                    logger.info(f"  - {members_by_id[member_id].name} now owes ${balances[member_id]['debts_by_member'][payer_id]:.2f} to {members_by_id[payer_id].name}")
                    logger.info(f"  - {members_by_id[member_id].name} total debt: ${balances[member_id]['total_debt']:.2f}")
                    logger.info(f"  - {members_by_id[payer_id].name} total owed: ${balances[payer_id]['total_owed']:.2f}")
        
        # Process payments
        # CORRECCIÓN: Asegurar que los pagos no se procesen por duplicado
        # Obtener todos los pagos confirmados de la familia
        all_payments = db.query(Payment).filter(
            and_(
                Payment.family_id == family_id,
                Payment.status == PaymentStatus.CONFIRM
            )
        ).all()
        
        # Crear un conjunto de IDs de pagos procesados para evitar duplicados
        processed_payment_ids = set()
        
        if debug_mode:
            logger.info(f"Found {len(all_payments)} confirmed payments to process")
        
        for payment in all_payments:
            # Verificar si ya hemos procesado este pago
            if payment.id in processed_payment_ids:
                if debug_mode:
                    logger.warning(f"Skipping already processed payment {payment.id}")
                continue
            
            # Marcar este pago como procesado
            processed_payment_ids.add(payment.id)
            
            from_member_id = str(payment.from_member_id)
            to_member_id = str(payment.to_member_id)
            amount = payment.amount
            payment_type = payment.payment_type
            
            # Determinar los roles según el tipo de pago
            if payment_type == PaymentType.PAYMENT:
                # Para pagos normales: from_member es el deudor, to_member es el acreedor
                debtor_id = from_member_id
                creditor_id = to_member_id
                debtor_name = members_by_id[from_member_id].name if from_member_id in members_by_id else "Unknown"
                creditor_name = members_by_id[to_member_id].name if to_member_id in members_by_id else "Unknown"
            else:  # PaymentType.ADJUSTMENT
                # Para ajustes de deuda: from_member es el acreedor, to_member es el deudor
                debtor_id = to_member_id
                creditor_id = from_member_id
                debtor_name = members_by_id[to_member_id].name if to_member_id in members_by_id else "Unknown"
                creditor_name = members_by_id[from_member_id].name if from_member_id in members_by_id else "Unknown"
            
            if debug_mode:
                if payment_type == PaymentType.PAYMENT:
                    logger.info(f"Processing payment: ${amount:.2f} from {debtor_name} to {creditor_name}")
                else:
                    logger.info(f"Processing debt adjustment: ${amount:.2f} from {creditor_name} to {debtor_name} (reducing debt)")
            
            # Verify that both members belong to the family
            if from_member_id in balances and to_member_id in balances:
                # Update the debt tracking
                if creditor_id in balances[debtor_id]["debts_by_member"]:
                    # Reduce the debt, don't go below zero
                    current_debt = balances[debtor_id]["debts_by_member"][creditor_id]
                    reduction = min(current_debt, amount)
                    balances[debtor_id]["debts_by_member"][creditor_id] -= reduction
                    
                    if debug_mode:
                        logger.info(f"  - Reducing {debtor_name}'s debt to {creditor_name} by ${reduction:.2f}")
                        logger.info(f"  - Debt before: ${current_debt:.2f}, after: ${balances[debtor_id]['debts_by_member'][creditor_id]:.2f}")
                    
                    # If debt is now zero, remove it entirely
                    if balances[debtor_id]["debts_by_member"][creditor_id] <= 0.001:  # Small threshold for float comparison
                        del balances[debtor_id]["debts_by_member"][creditor_id]
                        if debug_mode:
                            logger.info(f"  - Debt is now zero, removing from tracking")
                
                # Update the credit tracking
                if debtor_id in balances[creditor_id]["credits_by_member"]:
                    # Reduce the credit, don't go below zero
                    current_credit = balances[creditor_id]["credits_by_member"][debtor_id]
                    reduction = min(current_credit, amount)
                    balances[creditor_id]["credits_by_member"][debtor_id] -= reduction
                    
                    if debug_mode:
                        logger.info(f"  - Reducing {creditor_name}'s credit from {debtor_name} by ${reduction:.2f}")
                        logger.info(f"  - Credit before: ${current_credit:.2f}, after: ${balances[creditor_id]['credits_by_member'][debtor_id]:.2f}")
                    
                    # If credit is now zero, remove it entirely
                    if balances[creditor_id]["credits_by_member"][debtor_id] <= 0.001:  # Small threshold for float comparison
                        del balances[creditor_id]["credits_by_member"][debtor_id]
                        if debug_mode:
                            logger.info(f"  - Credit is now zero, removing from tracking")
                
                # Update the totals
                balances[debtor_id]["total_debt"] -= amount
                balances[creditor_id]["total_owed"] -= amount
                
                if debug_mode:
                    logger.info(f"  - {debtor_name} total debt reduced to ${balances[debtor_id]['total_debt']:.2f}")
                    logger.info(f"  - {creditor_name} total owed reduced to ${balances[creditor_id]['total_owed']:.2f}")
        
        # NUEVO: Netear deudas mutuas entre miembros
        if debug_mode:
            logger.info("Neteando deudas mutuas entre miembros")
            
        # Para cada par de miembros, netear sus deudas mutuas
        for member_id, balance_data in balances.items():
            member_name = balance_data["name"]
            
            # Obtener una copia de las claves para evitar modificar el diccionario durante la iteración
            debt_member_ids = list(balance_data["debts_by_member"].keys())
            
            for other_id in debt_member_ids:
                # Si este miembro debe al otro y el otro también le debe a este
                if other_id in balance_data["debts_by_member"] and member_id in balances[other_id]["debts_by_member"]:
                    other_name = balances[other_id]["name"]
                    
                    # Obtener las cantidades de deuda en ambas direcciones
                    debt_to_other = balance_data["debts_by_member"][other_id]
                    debt_from_other = balances[other_id]["debts_by_member"][member_id]
                    
                    if debug_mode:
                        logger.info(f"Encontrada deuda mutua: {member_name} debe ${debt_to_other:.2f} a {other_name}, y {other_name} debe ${debt_from_other:.2f} a {member_name}")
                    
                    # Calcular la deuda neta
                    if debt_to_other > debt_from_other:
                        # Este miembro debe más al otro
                        net_debt = debt_to_other - debt_from_other
                        
                        # Actualizar la deuda neta
                        balance_data["debts_by_member"][other_id] = net_debt
                        del balances[other_id]["debts_by_member"][member_id]  # El otro ya no debe nada
                        
                        if debug_mode:
                            logger.info(f"Deuda neta: {member_name} debe ${net_debt:.2f} a {other_name}")
                            
                    elif debt_from_other > debt_to_other:
                        # El otro miembro debe más a este
                        net_debt = debt_from_other - debt_to_other
                        
                        # Actualizar la deuda neta
                        balances[other_id]["debts_by_member"][member_id] = net_debt
                        del balance_data["debts_by_member"][other_id]  # Este ya no debe nada
                        
                        if debug_mode:
                            logger.info(f"Deuda neta: {other_name} debe ${net_debt:.2f} a {member_name}")
                            
                    else:
                        # Las deudas son iguales, se cancelan mutuamente
                        del balance_data["debts_by_member"][other_id]
                        del balances[other_id]["debts_by_member"][member_id]
                        
                        if debug_mode:
                            logger.info(f"Deudas iguales, se cancelan mutuamente entre {member_name} y {other_name}")
        
        # Recalcular los totales después del neteo
        for member_id, balance_data in balances.items():
            total_debt = sum(amount for amount in balance_data["debts_by_member"].values())
            total_owed = sum(balances[other_id]["debts_by_member"].get(member_id, 0.0) for other_id in balances)
            
            balance_data["total_debt"] = total_debt
            balance_data["total_owed"] = total_owed
            
            if debug_mode:
                logger.info(f"Totales recalculados para {balance_data['name']}: debe ${total_debt:.2f}, le deben ${total_owed:.2f}")
        
        # Limpiar completamente las listas de deudas y créditos para reconstruirlas de manera consistente
        for member_id, balance_data in balances.items():
            balance_data["debts"] = []
            balance_data["credits"] = []
        
        # Convert the debt and credit dictionaries to lists
        for member_id, balance_data in balances.items():
            # Convert debts_by_member to debts list
            for to_id, amount in balance_data["debts_by_member"].items():
                if amount > 0:
                    debt_detail = {
                        "to_id": to_id,
                        "to_name": members_by_id[to_id].name,
                        "amount": amount
                    }
                    balance_data["debts"].append(debt_detail)
            
            # Actualizar créditos basados en las deudas de otros miembros hacia este
            for other_id, other_balance in balances.items():
                if member_id in other_balance["debts_by_member"]:
                    amount = other_balance["debts_by_member"][member_id]
                    credit_detail = {
                        "from_id": other_id,
                        "from_name": other_balance["name"],
                        "amount": amount
                    }
                    balance_data["credits"].append(credit_detail)
        
        # Asegurarse de que todos los créditos y deudas estén correctamente procesados
        # antes de eliminar las estructuras temporales
        for member_id, balance_data in balances.items():
            # Ahora sí podemos limpiar las estructuras temporales
            del balance_data["debts_by_member"]
            del balance_data["credits_by_member"]
        
        # Calculate the net balance for each member
        for member_id, balance in balances.items():
            balance["net_balance"] = balance["total_owed"] - balance["total_debt"]
            if debug_mode:
                logger.info(f"{members_by_id[member_id].name} final net balance: ${balance['net_balance']:.2f}")
        
        # Verify balance consistency
        total_net_balance = sum(balance["net_balance"] for balance in balances.values())
        if debug_mode:
            logger.info(f"Total net balance across all members: ${total_net_balance:.2f}")
            if abs(total_net_balance) > 0.01:
                logger.warning(f"Warning: Total net balance is not zero (${total_net_balance:.2f})")
        
        # Convert to a list of MemberBalance objects
        result = []
        for member_id, balance_data in balances.items():
            member_balance = MemberBalance(
                member_id=balance_data["member_id"],
                name=balance_data["name"],
                total_debt=balance_data["total_debt"],
                total_owed=balance_data["total_owed"],
                net_balance=balance_data["net_balance"],
                debts=[DebtDetail(**debt) for debt in balance_data["debts"]],
                credits=[CreditDetail(**credit) for credit in balance_data["credits"]]
            )
            result.append(member_balance)
        
        return result
    
    @staticmethod
    def get_cached_balances(db: Session, family_id: str) -> List[MemberBalance]:
        """
        Obtiene los balances en caché para una familia.
        
        Args:
            db: Database session
            family_id: ID de la familia
            
        Returns:
            List[MemberBalance]: Lista de balances de miembros con detalles de deudas
        """
        logger.debug(f"Obteniendo balances en caché para familia: {family_id}")
        
        # Verificar si existe caché para todos los miembros de la familia
        member_ids = [m.id for m in db.query(Member).filter(Member.family_id == family_id).all()]
        cache_entries = db.query(MemberBalanceCache).filter(
            MemberBalanceCache.family_id == family_id,
            MemberBalanceCache.member_id.in_(member_ids)
        ).all()
        
        # Si no hay entrada de caché para cada miembro, debe calcularse desde cero
        if len(cache_entries) != len(member_ids):
            logger.debug(f"No hay caché completo para familia {family_id}. Inicializando caché...")
            return None
        
        # Crear diccionario de miembros para referencias
        members = db.query(Member).filter(Member.family_id == family_id).all()
        members_by_id = {str(m.id): m for m in members}
        
        # Obtener deudas en caché
        debt_cache = db.query(DebtCache).filter(DebtCache.family_id == family_id).all()
        
        # Organizar deudas por deudor
        debts_by_member = {}
        for debt in debt_cache:
            from_id = str(debt.from_member_id)
            to_id = str(debt.to_member_id)
            if from_id not in debts_by_member:
                debts_by_member[from_id] = []
            
            # Solo incluir deudas con valor mayor a cero
            if debt.amount > 0:
                debts_by_member[from_id].append({
                    "to_id": to_id,
                    "to_name": members_by_id[to_id].name if to_id in members_by_id else "Unknown",
                    "amount": debt.amount
                })
        
        # Construir lista de balances a partir del caché
        result_balances = []
        for cache in cache_entries:
            member_id = str(cache.member_id)
            member_name = members_by_id[member_id].name if member_id in members_by_id else "Unknown"
            
            # Construir deudas para este miembro
            debts = []
            if member_id in debts_by_member:
                for debt_info in debts_by_member[member_id]:
                    debts.append(DebtDetail(
                        to_id=debt_info["to_id"],
                        to_name=debt_info["to_name"],
                        amount=debt_info["amount"]
                    ))
            
            # Construir créditos
            credits = []
            for debt in debt_cache:
                if str(debt.to_member_id) == member_id and debt.amount > 0:
                    from_id = str(debt.from_member_id)
                    credits.append(CreditDetail(
                        from_id=from_id,
                        from_name=members_by_id[from_id].name if from_id in members_by_id else "Unknown",
                        amount=debt.amount
                    ))
            
            # Crear el objeto de balance
            balance = MemberBalance(
                member_id=member_id,
                member_name=member_name,
                net_balance=cache.net_balance,
                debts=debts,
                credits=credits
            )
            result_balances.append(balance)
        
        logger.info(f"Balances en caché obtenidos para familia {family_id}")
        return result_balances
    
    @staticmethod
    def initialize_balance_cache(db: Session, family_id: str) -> None:
        """
        Inicializa el caché de balances para una familia.
        
        Calcula los balances desde cero y los almacena en el caché.
        
        Args:
            db: Database session
            family_id: ID de la familia
        """
        logger.info(f"Inicializando caché de balances para familia: {family_id}")
        
        # Calcular balances desde cero
        balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Limpiar caché existente
        db.query(DebtCache).filter(DebtCache.family_id == family_id).delete()
        db.query(MemberBalanceCache).filter(MemberBalanceCache.family_id == family_id).delete()
        
        # Crear nuevas entradas de caché
        for balance in balances:
            # Crear entrada de caché de balance
            balance_cache = MemberBalanceCache(
                member_id=balance.member_id,
                family_id=family_id,
                total_debt=sum(d.amount for d in balance.debts),
                total_owed=sum(c.amount for c in balance.credits),
                net_balance=balance.net_balance
            )
            db.add(balance_cache)
            
            # Crear entradas de caché de deudas
            for debt in balance.debts:
                debt_cache = DebtCache(
                    family_id=family_id,
                    from_member_id=balance.member_id,  # deudor
                    to_member_id=debt.to_id,           # acreedor
                    amount=debt.amount
                )
                db.add(debt_cache)
        
        db.commit()
        logger.info(f"Caché de balances inicializado exitosamente para familia {family_id}")
    
    @staticmethod
    def update_cached_balances_for_expense(db: Session, expense: Expense) -> None:
        """
        Actualiza el caché de balances cuando se crea un nuevo gasto.
        
        Args:
            db: Database session
            expense: El gasto creado
        """
        logger.info(f"Actualizando caché de balances para nuevo gasto: {expense.id}")
        
        family_id = expense.family_id
        payer_id = expense.paid_by
        split_members = expense.split_among
        
        # Si no hay miembros específicos, dividir entre todos los miembros de la familia
        if not split_members:
            split_members = db.query(Member).filter(Member.family_id == family_id).all()
        
        # Calcular monto por miembro
        amount_per_member = expense.amount / len(split_members)
        
        # Obtener o crear caché para el pagador
        payer_cache = db.query(MemberBalanceCache).filter(
            MemberBalanceCache.member_id == payer_id,
            MemberBalanceCache.family_id == family_id
        ).first()
        
        if not payer_cache:
            # Si no hay caché, inicializar el caché completo
            BalanceService.initialize_balance_cache(db, family_id)
            return
        
        # Actualizar el balance del pagador
        payer_cache.total_owed += expense.amount - amount_per_member  # Restar su parte
        payer_cache.net_balance = payer_cache.total_owed - payer_cache.total_debt
        
        # Actualizar los balances de los miembros que comparten el gasto
        for member in split_members:
            # El pagador ya fue actualizado
            if member.id == payer_id:
                continue
                
            # Obtener o crear caché para este miembro
            member_cache = db.query(MemberBalanceCache).filter(
                MemberBalanceCache.member_id == member.id,
                MemberBalanceCache.family_id == family_id
            ).first()
            
            if not member_cache:
                # Si falta algún miembro, inicializar todo el caché
                BalanceService.initialize_balance_cache(db, family_id)
                return
            
            # Actualizar el balance del miembro
            member_cache.total_debt += amount_per_member
            member_cache.net_balance = member_cache.total_owed - member_cache.total_debt
            
            # Actualizar o crear deuda específica
            debt = db.query(DebtCache).filter(
                DebtCache.family_id == family_id,
                DebtCache.from_member_id == member.id,
                DebtCache.to_member_id == payer_id
            ).first()
            
            if debt:
                debt.amount += amount_per_member
            else:
                debt = DebtCache(
                    family_id=family_id,
                    from_member_id=member.id,
                    to_member_id=payer_id,
                    amount=amount_per_member
                )
                db.add(debt)
        
        db.commit()
        logger.info(f"Caché de balances actualizado para nuevo gasto: {expense.id}")
    
    @staticmethod
    def update_cached_balances_for_payment(db: Session, payment: Payment) -> None:
        """
        Actualiza el caché de balances cuando se confirma un pago.
        
        Args:
            db: Database session
            payment: El pago confirmado
        """
        # Solo procesar pagos confirmados
        if payment.status != PaymentStatus.CONFIRM:
            return
            
        logger.info(f"Actualizando caché de balances para pago confirmado: {payment.id}")
        
        family_id = payment.family_id
        amount = payment.amount
        payment_type = payment.payment_type
        
        # Determinar quién es el deudor y quién es el acreedor según el tipo de pago
        if payment_type == PaymentType.PAYMENT:
            # En un pago normal, from_member es el deudor, to_member es el acreedor
            debtor_id = payment.from_member_id
            creditor_id = payment.to_member_id
        else:  # PaymentType.ADJUSTMENT
            # En un ajuste de deuda, from_member es el acreedor, to_member es el deudor
            debtor_id = payment.to_member_id
            creditor_id = payment.from_member_id
        
        # Obtener caché de balances para ambos miembros
        debtor_cache = db.query(MemberBalanceCache).filter(
            MemberBalanceCache.member_id == debtor_id,
            MemberBalanceCache.family_id == family_id
        ).first()
        
        creditor_cache = db.query(MemberBalanceCache).filter(
            MemberBalanceCache.member_id == creditor_id,
            MemberBalanceCache.family_id == family_id
        ).first()
        
        # Si algún caché no existe, inicializar todo el caché
        if not debtor_cache or not creditor_cache:
            BalanceService.initialize_balance_cache(db, family_id)
            return
        
        # Obtener la deuda específica
        debt = db.query(DebtCache).filter(
            DebtCache.family_id == family_id,
            DebtCache.from_member_id == debtor_id,
            DebtCache.to_member_id == creditor_id
        ).first()
        
        # Si no hay registro de deuda, inicializar todo el caché para asegurar coherencia
        if not debt and amount > 0:
            BalanceService.initialize_balance_cache(db, family_id)
            return
        
        # Actualizar la deuda específica
        if debt:
            # Reducir la deuda, pero no por debajo de cero
            reduction = min(debt.amount, amount)
            debt.amount -= reduction
            
            # Si la deuda es ahora cero, eliminarla
            if debt.amount <= 0.001:  # Umbral pequeño para comparación de punto flotante
                db.delete(debt)
        
        # Actualizar los balances de los miembros
        debtor_cache.total_debt -= amount
        debtor_cache.net_balance = debtor_cache.total_owed - debtor_cache.total_debt
        
        creditor_cache.total_owed -= amount
        creditor_cache.net_balance = creditor_cache.total_owed - creditor_cache.total_debt
        
        db.commit()
        logger.info(f"Caché de balances actualizado para pago: {payment.id}")
    
    @staticmethod
    def get_family_balances(db: Session, family_id: str, use_cache: bool = True, force_refresh: bool = False) -> List[MemberBalance]:
        """
        Obtiene los balances de una familia, usando caché si está disponible.
        
        Args:
            db: Database session
            family_id: ID de la familia
            use_cache: Si es True, intentará usar el caché; si es False, calculará desde cero
            force_refresh: Si es True, recalculará y refrescará el caché
            
        Returns:
            List[MemberBalance]: Lista de balances de miembros
        """
        # Si se solicita refresh o no se debe usar caché, calcular desde cero
        if force_refresh or not use_cache:
            if force_refresh:
                logger.info(f"Forzando actualización del caché para familia: {family_id}")
                balances = BalanceService.calculate_family_balances(db, family_id)
                BalanceService.initialize_balance_cache(db, family_id)
                return balances
            else:
                logger.info(f"Caché desactivado, calculando balances para familia: {family_id}")
                return BalanceService.calculate_family_balances(db, family_id)
        
        # Intentar obtener del caché
        cached_balances = BalanceService.get_cached_balances(db, family_id)
        
        # Si no hay caché completo, inicializarlo y retornar
        if not cached_balances:
            logger.info(f"No hay caché disponible para familia: {family_id}, inicializando")
            BalanceService.initialize_balance_cache(db, family_id)
            return BalanceService.get_cached_balances(db, family_id)
        
        return cached_balances
    
    @staticmethod
    def get_member_balance(db: Session, family_id: str, member_id: str) -> MemberBalance:
        """
        Get the balance of a specific member.
        
        Args:
            db: Database session
            family_id: ID of the family the member belongs to
            member_id: ID of the member to get the balance for
            
        Returns:
            MemberBalance: The member's balance or None if not found
        """
        # Calculate the balances of the entire family
        family_balances = BalanceService.calculate_family_balances(db, family_id)
        
        # Find the balance of the specific member
        for balance in family_balances:
            if balance.member_id == str(member_id):
                return balance
        
        return None
        
    @staticmethod
    def verify_balance_consistency(db: Session, family_id: str) -> bool:
        """
        Verify that the total net balance of all family members is zero.
        
        Args:
            db: Database session
            family_id: ID of the family to verify
            
        Returns:
            bool: True if consistent (sum of balances is approximately zero), False otherwise
        """
        balances = BalanceService.calculate_family_balances(db, family_id)
        total_net_balance = sum(balance.net_balance for balance in balances)
        
        # Allow for small floating point errors
        return abs(total_net_balance) < 0.01
        
    @staticmethod
    def debug_payment_handling(db: Session, family_id: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Analiza detalladamente cómo se están procesando los pagos para diagnosticar problemas.
        
        Args:
            db: Database session
            family_id: ID de la familia a analizar
            
        Returns:
            Tuple[List[Dict], List[Dict]]: Una tupla que contiene:
                1. Lista de todos los pagos en la familia
                2. Lista de diagnóstico de cómo se procesaron los pagos
        """
        # Obtener todos los miembros de la familia
        members = db.query(Member).filter(Member.family_id == family_id).all()
        members_by_id = {str(m.id): m for m in members}
        
        # Obtener todos los pagos relacionados con la familia
        payments_from = db.query(Payment).filter(
            Payment.from_member_id.in_([m.id for m in members])
        ).all()
        
        payments_to = db.query(Payment).filter(
            Payment.to_member_id.in_([m.id for m in members])
        ).all()
        
        # Unir los pagos y eliminar duplicados
        all_payments = []
        seen_payment_ids = set()
        
        for payment in payments_from + payments_to:
            if payment.id not in seen_payment_ids:
                seen_payment_ids.add(payment.id)
                all_payments.append({
                    "id": payment.id,
                    "from_member": members_by_id[payment.from_member_id].name if payment.from_member_id in members_by_id else "Unknown",
                    "to_member": members_by_id[payment.to_member_id].name if payment.to_member_id in members_by_id else "Unknown",
                    "amount": payment.amount,
                    "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(payment, "created_at") else "Unknown"
                })
        
        # Calcular balances usando el método normal pero con debug activado
        # Esto generará logs detallados sobre el procesamiento de pagos
        BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Diagnóstico adicional: Detectar posibles pagos duplicados
        duplicate_analysis = []
        payment_signatures = {}  # signature -> count
        
        for payment in all_payments:
            # Crear una firma para detectar pagos similares
            signature = f"{payment['from_member']}->{payment['to_member']}-{payment['amount']}"
            
            if signature in payment_signatures:
                payment_signatures[signature].append(payment["id"])
            else:
                payment_signatures[signature] = [payment["id"]]
        
        # Añadir al diagnóstico los pagos posiblemente duplicados
        for signature, ids in payment_signatures.items():
            if len(ids) > 1:
                from_member, to_member, amount = signature.split("->")[0], signature.split("->")[1].split("-")[0], signature.split("-")[-1]
                duplicate_analysis.append({
                    "possible_duplicate": True,
                    "from_member": from_member,
                    "to_member": to_member,
                    "amount": amount,
                    "payment_ids": ids,
                    "count": len(ids),
                    "recommendation": "Verificar si estos pagos son duplicados accidentales"
                })
        
        return all_payments, duplicate_analysis 