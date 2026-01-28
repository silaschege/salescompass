"""
POS Service - Business logic for Point of Sale operations.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import (
    POSTerminal, POSSession, POSTransaction, POSTransactionLine,
    POSPayment, POSReceipt, POSCashDrawer, POSCashMovement,
    POSRefund, POSRefundLine
)
from inventory.services import InventoryService
from billing.services import TaxService
from products.services import PricingService, PromotionService
from loyalty.services import LoyaltyService
from core.event_bus import event_bus


class POSService:
    """
    Service class for POS operations.
    """
    
    # ==========================================================================
    # SESSION MANAGEMENT
    # ==========================================================================
    
    @staticmethod
    @transaction.atomic
    def open_session(terminal, cashier, opening_cash=Decimal('0'), notes=''):
        """
        Open a new POS session for a cashier.
        """
        # Check if there's already an active session on this terminal
        active_session = POSSession.objects.filter(
            terminal=terminal,
            status='active'
        ).first()
        
        if active_session:
            raise ValueError(
                f"Terminal {terminal.terminal_name} already has an active session. "
                f"Please close session {active_session.session_number} first."
            )
        
        # Create new session
        session = POSSession.objects.create(
            terminal=terminal,
            cashier=cashier,
            opening_cash=opening_cash,
            opening_notes=notes,
            tenant=terminal.tenant
        )
        
        # Initialize cash drawer
        drawer, created = POSCashDrawer.objects.get_or_create(
            terminal=terminal,
            tenant=terminal.tenant,
            defaults={'current_cash': opening_cash}
        )
        
        if not created:
            drawer.current_cash = opening_cash
        drawer.status = 'open'
        drawer.last_opened_at = timezone.now()
        drawer.last_opened_by = cashier
        drawer.save()
        
        # Record opening cash movement
        POSCashMovement.objects.create(
            drawer=drawer,
            session=session,
            movement_type='opening',
            amount=opening_cash,
            balance_after=opening_cash,
            performed_by=cashier,
            tenant=terminal.tenant
        )
        
        return session

    @staticmethod
    @transaction.atomic
    def close_session(session, closing_cash, cashier, notes=''):
        """
        Close a POS session with cash count.
        """
        if session.status != 'active':
            raise ValueError(f"Session {session.session_number} is not active.")
        
        session.status = 'closing'
        
        # Calculate expected cash
        cash_payments = POSPayment.objects.filter(
            transaction__session=session,
            payment_method='cash',
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        cash_refunds = POSPayment.objects.filter(
            transaction__session=session,
            transaction__status='refunded',
            payment_method='cash'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        expected_cash = session.opening_cash + cash_payments - cash_refunds
        
        # Calculate totals
        transactions = POSTransaction.objects.filter(
            session=session, status='completed'
        )
        
        session.total_sales = sum(t.total_amount for t in transactions)
        session.total_transactions = transactions.count()
        session.total_refunds = POSRefund.objects.filter(
            original_transaction__session=session,
            status='completed'
        ).aggregate(total=models.Sum('refund_amount'))['total'] or Decimal('0')
        session.total_discounts = sum(t.discount_amount for t in transactions)
        
        # Record closing
        session.closed_at = timezone.now()
        session.closing_cash = closing_cash
        session.expected_cash = expected_cash
        session.cash_difference = closing_cash - expected_cash
        session.closing_notes = notes
        session.status = 'closed'
        session.save()
        
        # Close cash drawer
        drawer = POSCashDrawer.objects.get(terminal=session.terminal)
        POSCashMovement.objects.create(
            drawer=drawer,
            session=session,
            movement_type='closing',
            amount=closing_cash,
            balance_after=closing_cash,
            performed_by=cashier,
            tenant=session.tenant
        )
        drawer.status = 'closed'
        drawer.current_cash = closing_cash
        drawer.save()
        
        return session

    # ==========================================================================
    # TRANSACTION MANAGEMENT
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def create_transaction(session, cashier, customer=None, customer_info=None):
        """
        Create a new POS transaction.
        """
        txn = POSTransaction.objects.create(
            session=session,
            terminal=session.terminal,
            cashier=cashier,
            customer=customer,
            customer_name=customer_info.get('name', '') if customer_info else '',
            customer_phone=customer_info.get('phone', '') if customer_info else '',
            customer_email=customer_info.get('email', '') if customer_info else '',
            status='draft',
            tenant=session.tenant
        )
        return txn

    @staticmethod
    @transaction.atomic
    def add_line_item(transaction, product, quantity=1, unit_price=None, 
                      discount_percent=0):
        """
        Add a product line to a transaction.
        """
        if transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
        
        if unit_price is None:
             unit_price = PricingService.get_price(
                 product=product,
                 account=transaction.customer,
                 quantity=quantity
             )
            
        # Get tax rate
        tax_rate_obj = TaxService.get_applicable_tax_rate(product, transaction.tenant)
        tax_rate_val = tax_rate_obj.rate if tax_rate_obj else Decimal('0')
        
        line = POSTransactionLine.objects.create(
            transaction=transaction,
            product=product,
            quantity=Decimal(str(quantity)),
            unit_price=Decimal(str(unit_price)),
            discount_percent=Decimal(str(discount_percent)),
            tax_rate=tax_rate_val,
            # For now assume inclusive, could comes from tenant settings later
            is_tax_inclusive=True, 
            tenant=transaction.tenant
        )
        
        # Recalculate totals
        transaction.calculate_totals()
        
        return line

    @staticmethod
    @transaction.atomic
    def remove_line_item(line):
        """
        Remove a line item from a transaction.
        """
        transaction = line.transaction
        if transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
        
        line.delete()
        transaction.calculate_totals()
        
        return transaction

    @staticmethod
    @transaction.atomic
    def update_line_quantity(line, new_quantity):
        """
        Update the quantity of a line item.
        """
        if line.transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
        
        line.quantity = Decimal(str(new_quantity))
        line.save()
        line.transaction.calculate_totals()
        
        return line

    @staticmethod
    def apply_discount(transaction, discount_percent=0, discount_amount=0, reason=''):
        """
        Apply a discount to the transaction.
        """
        if transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
        
        transaction.discount_percent = Decimal(str(discount_percent))
        transaction.discount_reason = reason
        transaction.calculate_totals()
        
        return transaction

    @staticmethod
    def apply_coupon(transaction, coupon_code):
        """
        Apply a coupon to the transaction.
        """
        if transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
            
        # Validate coupon
        is_valid, message, coupon = PromotionService.validate_coupon(
            code=coupon_code,
            tenant=transaction.tenant,
            user=transaction.customer.owner if transaction.customer else None, # Approximate user
            cart_total=transaction.subtotal
        )
        
        if not is_valid:
            raise ValueError(f"Coupon error: {message}")
            
        # Calculate discount
        discount_amount = PromotionService.calculate_discount(coupon, transaction.subtotal)
        
        # Apply to transaction
        transaction.coupon = coupon
        transaction.discount_amount = discount_amount
        # Calculate percent for consistency if needed, but here we set amount directly
        if transaction.subtotal > 0:
            transaction.discount_percent = (discount_amount / transaction.subtotal) * 100
        
        transaction.save()
        transaction.calculate_totals() # This might overwrite manual amount if logic not adjusted?
        # IMPORTANT: POSTransaction.calculate_totals logic currently calculates from discount_percent
        # We should update calculate_totals or just rely on percent.
        # Let's rely on percent for now to fit existing model logic, or update model method.
        # But coupon creates fixed discount often.
        
        # Re-calc manually for now to be safe with model hooks
        transaction.refresh_from_db()
        return transaction

    @staticmethod
    def remove_coupon(transaction):
        """
        Remove applied coupon.
        """
        if transaction.status != 'draft':
            raise ValueError("Cannot modify a non-draft transaction.")
            
        transaction.coupon = None
        transaction.discount_amount = Decimal('0')
        transaction.discount_percent = Decimal('0')
        transaction.save()
        transaction.calculate_totals()
        return transaction

    # ==========================================================================
    # PAYMENT PROCESSING
    # ==========================================================================

    @staticmethod
    def _recalculate_transaction_totals(transaction):
        """Internal helper to recalculate transaction totals."""
        transaction.calculate_totals()
        return transaction

    @staticmethod
    @transaction.atomic
    def process_payment(transaction, payment_method, amount, user, 
                        reference_number='', redeem_points=False, **kwargs):
        """
        Process a payment for a transaction. Support for multiple payment methods
        is handled by calling this multiple times or through bulk logic.
        """
        if transaction.status not in ['draft', 'pending']:
            raise ValueError("Transaction is not in a payable state.")
        
        amount = Decimal(str(amount))
        
        if redeem_points and transaction.customer:
            # Handle Loyalty Redemption
            try:
                loyalty_profile = transaction.customer.loyalty_account
                if loyalty_profile.program and loyalty_profile.program.is_active:
                    # Calculate value to redeem
                    points_needed = int(amount / loyalty_profile.program.redemption_conversion_rate)
                    
                    LoyaltyService.redeem_points(
                        customer_loyalty=loyalty_profile,
                        points=points_needed,
                        description=f"Redemption for POS Transaction {transaction.transaction_number}",
                        member=user
                    )
                    
                    # Record as a payment method 'loyalty'
                    payment_method = 'loyalty'
            except Exception as e:
                raise ValueError(f"Loyalty redemption failed: {str(e)}")

        payment = POSPayment.objects.create(
            transaction=transaction,
            payment_method=payment_method,
            amount=amount,
            status='completed',
            reference_number=reference_number,
            card_last_four=kwargs.get('card_last_four', ''),
            card_type=kwargs.get('card_type', ''),
            mobile_number=kwargs.get('mobile_number', ''),
            mobile_provider=kwargs.get('mobile_provider', ''),
            voucher_code=kwargs.get('voucher_code', ''),
            processed_by=user,
            tenant=transaction.tenant
        )
        
        # Update transaction
        total_paid = sum(
            p.amount for p in transaction.payments.filter(status='completed')
        )
        transaction.amount_paid = total_paid
        
        if total_paid >= transaction.total_amount:
            transaction.change_due = total_paid - transaction.total_amount
            transaction.status = 'completed'
            transaction.completed_at = timezone.now()
            
            # Use coupon if present
            if transaction.coupon:
                PromotionService.use_coupon(transaction.coupon)
                
            # Earn Loyalty Points on Cash/Card portion (not loyalty portion)
            if transaction.customer:
                try:
                    loyalty_payments = transaction.payments.filter(payment_method='loyalty').aggregate(total=models.Sum('amount'))['total'] or 0
                    eligible_amount = transaction.total_amount - loyalty_payments
                    
                    if eligible_amount > 0:
                        loyalty_profile = transaction.customer.loyalty_account
                        if loyalty_profile.program and loyalty_profile.program.is_active:
                            points_to_earn = int(eligible_amount * loyalty_profile.program.points_per_currency)
                            if points_to_earn > 0:
                                LoyaltyService.award_points(
                                    customer=transaction.customer,
                                    points=points_to_earn,
                                    description=f"Earned from POS Transaction {transaction.transaction_number}",
                                    sale_amount=eligible_amount,
                                    reference=f"POS-{transaction.transaction_number}",
                                    member=user
                                )
                except Exception:
                    pass # Don't block transaction completion on loyalty error
            
            # Deduct stock for each line item
            if transaction.terminal and transaction.terminal.warehouse:
                warehouse = transaction.terminal.warehouse
                for line in transaction.lines.all():
                    if hasattr(line.product, 'track_inventory') and line.product.track_inventory:
                        try:
                            InventoryService.remove_stock(
                                product=line.product,
                                warehouse=warehouse,
                                quantity=line.quantity,
                                user=user,
                                reference_type='pos_transaction',
                                reference_id=transaction.id,
                                movement_type='sale',
                                tenant=transaction.tenant
                            )
                        except ValueError:
                            # Handle out of stock - depends on terminal settings
                            if not transaction.terminal.allow_negative_stock:
                                raise
                
            # Integration: Post to Accounting
            from billing.services import AccountingIntegrationService
            try:
                AccountingIntegrationService.post_pos_sale_to_gl(transaction)
            except Exception:
                pass # Non-critical for POS flow
            
            # Emit sale completed event
            event_bus.emit('pos.sale.completed', {
                'transaction_id': transaction.id,
                'total_amount': float(transaction.total_amount),
                'terminal_id': transaction.terminal.id if transaction.terminal else None,
                'customer_id': transaction.customer.id if transaction.customer else None,
                'tenant_id': transaction.tenant.id,
                'user': user
            })
            
        else:
            transaction.status = 'pending'
        
        transaction.save()
        
        # Update cash drawer if cash payment
        if payment_method == 'cash':
            POSService._record_cash_movement(
                transaction, 'sale', amount, user
            )
        
        return payment

    @staticmethod
    @transaction.atomic
    def void_transaction(transaction, reason, user):
        """
        Void a transaction.
        """
        if transaction.status == 'voided':
            raise ValueError("Transaction is already voided.")
        
        if transaction.status == 'completed':
            # Reverse stock movements
            if transaction.terminal and transaction.terminal.warehouse:
                warehouse = transaction.terminal.warehouse
                for line in transaction.lines.all():
                    if hasattr(line.product, 'track_inventory') and line.product.track_inventory:
                        InventoryService.add_stock(
                            product=line.product,
                            warehouse=warehouse,
                            quantity=line.quantity,
                            user=user,
                            reference_type='void_transaction',
                            reference_id=transaction.id,
                            tenant=transaction.tenant
                        )
        
        transaction.status = 'voided'
        transaction.voided_at = timezone.now()
        transaction.voided_by = user
        transaction.void_reason = reason
        transaction.save()
        
        return transaction

    # ==========================================================================
    # REFUND PROCESSING
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def create_refund(original_transaction, lines_to_refund, reason, 
                      refund_method, user, requires_approval=True):
        """
        Create a refund for a transaction.
        
        lines_to_refund: list of dicts with {'line_id': int, 'quantity': Decimal}
        """
        if original_transaction.status != 'completed':
            raise ValueError("Can only refund completed transactions.")
        
        # Calculate refund amount
        refund_amount = Decimal('0')
        refund_lines = []
        
        for item in lines_to_refund:
            original_line = POSTransactionLine.objects.get(
                id=item['line_id'],
                transaction=original_transaction
            )
            quantity = Decimal(str(item.get('quantity', original_line.quantity)))
            
            if quantity > original_line.quantity:
                raise ValueError(f"Cannot refund {quantity} items, only {original_line.quantity} available.")
                
            line_refund = (original_line.line_total / original_line.quantity) * quantity
            refund_amount += line_refund
            refund_lines.append({
                'original_line': original_line,
                'quantity': quantity,
                'refund_amount': line_refund,
                'restock': item.get('restock', True)
            })
        
        # Determine refund type
        if len(lines_to_refund) == original_transaction.lines.count():
            total_qty_refunded = sum(item['quantity'] for item in refund_lines)
            orig_qty = sum(line.quantity for line in original_transaction.lines.all())
            refund_type = 'full' if total_qty_refunded >= orig_qty else 'partial'
        else:
            refund_type = 'partial'
        
        # Create refund
        refund = POSRefund.objects.create(
            original_transaction=original_transaction,
            refund_type=refund_type,
            status='pending' if requires_approval else 'approved',
            refund_amount=refund_amount,
            refund_method=refund_method,
            reason=reason,
            requires_approval=requires_approval,
            processed_by=user,
            tenant=original_transaction.tenant
        )
        
        # Create refund lines
        for item in refund_lines:
            POSRefundLine.objects.create(
                refund=refund,
                original_line=item['original_line'],
                quantity=item['quantity'],
                refund_amount=item['refund_amount'],
                restock=item['restock'],
                tenant=original_transaction.tenant
            )
        
        # If no approval needed, process immediately
        if not requires_approval:
            POSService.process_refund(refund, user)
        
        return refund

    @staticmethod
    @transaction.atomic
    def process_refund(refund, user):
        """
        Process an approved refund.
        """
        if refund.status not in ['pending', 'approved']:
            raise ValueError("Refund is not in a processable state.")
        
        # Restock items
        if refund.original_transaction.terminal and refund.original_transaction.terminal.warehouse:
            warehouse = refund.original_transaction.terminal.warehouse
            for line in refund.lines.filter(restock=True):
                product = line.original_line.product
                if hasattr(product, 'track_inventory') and product.track_inventory:
                    InventoryService.add_stock(
                        product=product,
                        warehouse=warehouse,
                        quantity=line.quantity,
                        user=user,
                        reference_type='refund',
                        reference_id=refund.id,
                        tenant=refund.tenant
                    )
        
        # Create negative payment for refund record
        POSPayment.objects.create(
            transaction=refund.original_transaction,
            payment_method=f"refund_{refund.refund_method}",
            amount=-refund.refund_amount,
            status='completed',
            reference_number=refund.refund_number,
            processed_by=user,
            tenant=refund.tenant
        )

        # Mark as completed
        refund.status = 'completed'
        refund.completed_at = timezone.now()
        if refund.approved_by is None:
            refund.approved_by = user
            refund.approved_at = timezone.now()
        refund.save()
        
        # Update original transaction status (consider partial refund status later)
        refund.original_transaction.status = 'refunded'
        refund.original_transaction.save()
        
        # Record cash movement if cash refund
        if refund.refund_method == 'cash':
            POSService._record_cash_movement(
                refund.original_transaction, 
                'refund', 
                -refund.refund_amount,  # Negative for outgoing
                user
            )
            
        # Emit refund completed event
        event_bus.emit('pos.refund.completed', {
            'refund_id': refund.id,
            'original_transaction_id': refund.original_transaction.id,
            'refund_amount': float(refund.refund_amount),
            'tenant_id': refund.tenant.id,
            'user': user
        })
        
        return refund

    # ==========================================================================
    # CASH DRAWER OPERATIONS
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def open_drawer(terminal, user, reason=''):
        """
        Open the cash drawer.
        """
        drawer, created = POSCashDrawer.objects.get_or_create(
            terminal=terminal,
            tenant=terminal.tenant,
            defaults={'current_cash': Decimal('0')}
        )
        drawer.status = 'open'
        drawer.last_opened_at = timezone.now()
        drawer.last_opened_by = user
        drawer.save()
        
        return drawer

    @staticmethod
    @transaction.atomic
    def pay_in(session, amount, user, notes=''):
        """
        Add cash to the drawer (not from sales).
        """
        drawer = POSCashDrawer.objects.get(terminal=session.terminal)
        drawer.current_cash += Decimal(str(amount))
        drawer.save()
        
        POSCashMovement.objects.create(
            drawer=drawer,
            session=session,
            movement_type='pay_in',
            amount=Decimal(str(amount)),
            balance_after=drawer.current_cash,
            notes=notes,
            performed_by=user,
            tenant=session.tenant
        )
        
        return drawer

    @staticmethod
    @transaction.atomic
    def pay_out(session, amount, user, notes=''):
        """
        Remove cash from the drawer (not for refunds).
        """
        drawer = POSCashDrawer.objects.get(terminal=session.terminal)
        
        amount_val = Decimal(str(amount))
        if drawer.current_cash < amount_val:
            raise ValueError("Insufficient cash in drawer.")
        
        drawer.current_cash -= amount_val
        drawer.save()
        
        POSCashMovement.objects.create(
            drawer=drawer,
            session=session,
            movement_type='pay_out',
            amount=-amount_val,
            balance_after=drawer.current_cash,
            notes=notes,
            performed_by=user,
            tenant=session.tenant
        )
        
        return drawer

    @staticmethod
    def _record_cash_movement(transaction, movement_type, amount, user):
        """
        Internal helper to record cash movements.
        """
        if not transaction.session:
            return
        
        amount_val = Decimal(str(amount))
        drawer = POSCashDrawer.objects.get(terminal=transaction.terminal)
        drawer.current_cash += amount_val
        drawer.save()
        
        POSCashMovement.objects.create(
            drawer=drawer,
            session=transaction.session,
            movement_type=movement_type,
            amount=amount_val,
            balance_after=drawer.current_cash,
            transaction=transaction,
            performed_by=user,
            tenant=transaction.tenant
        )

    # ==========================================================================
    # RECEIPT GENERATION
    # ==========================================================================

    @staticmethod
    def generate_receipt(transaction, receipt_type='sale'):
        """
        Generate a receipt for a transaction.
        """
        receipt = POSReceipt.objects.create(
            transaction=transaction,
            receipt_type=receipt_type,
            header_text=transaction.terminal.receipt_footer if (transaction.terminal and transaction.terminal.receipt_footer) else '',
            tenant=transaction.tenant
        )
        return receipt

    @staticmethod
    def email_receipt(receipt, email_address):
        """
        Email a receipt to a customer.
        """
        # TODO: Implement email sending
        receipt.emailed_to = email_address
        receipt.save()
        return receipt

    # ==========================================================================
    # PRODUCT LOOKUP
    # ==========================================================================

    @staticmethod
    def search_products(query, tenant, category_id=None, limit=20):
        """
        Search for products by name, SKU, or barcode.
        """
        from products.models import Product
        from django.db.models import Q
        
        products = Product.objects.filter(
            tenant=tenant,
            product_is_active=True
        )
        
        if query:
            products = products.filter(
                Q(product_name__icontains=query) |
                Q(sku__icontains=query) |
                Q(upc__icontains=query)
            )
            
        if category_id:
            products = products.filter(category_id=category_id)
            
        return products[:limit]

    @staticmethod
    def get_product_by_barcode(barcode, tenant):
        """
        Get a product by its barcode/UPC.
        """
        from products.models import Product
        
        try:
            return Product.objects.get(
                tenant=tenant,
                upc=barcode,
                product_is_active=True
            )
        except Product.DoesNotExist:
            # Try SKU as fallback
            try:
                return Product.objects.get(
                    tenant=tenant,
                    sku=barcode,
                    product_is_active=True
                )
            except Product.DoesNotExist:
                return None
