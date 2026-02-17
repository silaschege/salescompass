from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import StockAdjustment, StockAdjustmentLine
from accounting.services import JournalService
from accounting.models import AccountingIntegration
from decimal import Decimal


# ============================================================================
# STOCK ADJUSTMENT INTEGRATION
# ============================================================================

@receiver(post_save, sender=StockAdjustment)
def handle_stock_adjustment_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when stock adjustment is applied.
    
    For Losses (negative variance):
    Dr: Shrinkage/Loss Expense Account
    Cr: Inventory Account
    
    For Gains (positive variance):
    Dr: Inventory Account
    Cr: Inventory Gain/Adjustment Account
    """
    # Only process when adjustment is applied
    if instance.status != 'applied':
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    # Calculate total variance value
    total_loss = Decimal('0')
    total_gain = Decimal('0')
    
    for line in instance.lines.all():
        variance_qty = line.actual_quantity - line.system_quantity
        
        # Get cost price from stock level
        try:
            from .models import StockLevel
            stock_level = StockLevel.objects.get(
                product=line.product,
                warehouse=instance.warehouse,
                tenant=instance.tenant
            )
            cost_price = stock_level.cost_price or Decimal('0')
        except StockLevel.DoesNotExist:
            # If no stock level, try to get from product
            cost_price = getattr(line.product, 'cost_price', Decimal('0'))
        
        # Calculate value
        variance_value = variance_qty * cost_price
        
        if variance_value < 0:
            total_loss += abs(variance_value)
        elif variance_value > 0:
            total_gain += variance_value
    
    # Process losses
    if total_loss > 0:
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='inventory_loss'
            )
            
            lines = [
                {
                    'account': config.debit_account,  # Shrinkage/Loss Expense
                    'debit': total_loss,
                    'credit': 0,
                    'description': f"Inventory Loss: {instance.adjustment_number} - {instance.get_reason_display()}"
                },
                {
                    'account': config.credit_account,  # Inventory
                    'debit': 0,
                    'credit': total_loss,
                    'description': f"Stock adjustment: {instance.warehouse.warehouse_name}"
                }
            ]
            
            journal_entry = JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.approved_at.date() if instance.approved_at else instance.created_at.date(),
                description=f"Inventory Loss: {instance.adjustment_number}",
                user=instance.approved_by,
                lines=lines,
                reference=instance.adjustment_number,
                status='posted'
            )
            
            # Link journal entry
            instance.journal_entry = journal_entry
            instance._skip_signal = True
            instance.save(update_fields=['journal_entry'])
            
        except AccountingIntegration.DoesNotExist:
            print(f"[Accounting] No integration configured for inventory_loss (Tenant: {instance.tenant})")
    
    # Process gains
    if total_gain > 0:
        try:
            config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='inventory_gain'
            )
            
            lines = [
                {
                    'account': config.debit_account,  # Inventory
                    'debit': total_gain,
                    'credit': 0,
                    'description': f"Inventory Gain: {instance.adjustment_number}"
                },
                {
                    'account': config.credit_account,  # Inventory Gain/Adjustment
                    'debit': 0,
                    'credit': total_gain,
                    'description': f"Stock count adjustment: {instance.warehouse.warehouse_name}"
                }
            ]
            
            journal_entry = JournalService.create_journal_entry(
                tenant=instance.tenant,
                date=instance.approved_at.date() if instance.approved_at else instance.created_at.date(),
                description=f"Inventory Gain: {instance.adjustment_number}",
                user=instance.approved_by,
                lines=lines,
                reference=instance.adjustment_number,
                status='posted'
            )
            
            # Link journal entry if not already linked (from loss)
            if not instance.journal_entry:
                instance.journal_entry = journal_entry
                instance._skip_signal = True
                instance.save(update_fields=['journal_entry'])
            
        except AccountingIntegration.DoesNotExist:
            print(f"[Accounting] No integration configured for inventory_gain (Tenant: {instance.tenant})")
