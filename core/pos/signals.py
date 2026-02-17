from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import POSTransaction
from accounting.services import JournalService
from accounting.models import AccountingIntegration
from decimal import Decimal


# ============================================================================
# POS COST OF GOODS SOLD (COGS) INTEGRATION
# ============================================================================

@receiver(post_save, sender=POSTransaction)
def handle_pos_cogs_integration(sender, instance, created, **kwargs):
    """
    Trigger journal entry for Cost of Goods Sold when POS transaction completes.
    
    Accounting Entry:
    Dr: Cost of Goods Sold Account
    Cr: Inventory Account
    
    Note: This is separate from the revenue entry created in accounting/signals.py
    """
    # Only process completed transactions
    if instance.status != 'completed':
        return
    
    # Skip if we're in a signal loop
    if getattr(instance, '_skip_cogs_signal', False):
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='pos_sale'  # Use same event type, different accounts
        )
        
        # Calculate total COGS from transaction lines
        total_cogs = Decimal('0')
        
        for line in instance.lines.all():
            # Get cost price from stock level
            try:
                from inventory.models import StockLevel
                stock_level = StockLevel.objects.filter(
                    product=line.product,
                    warehouse=instance.terminal.warehouse if instance.terminal else None,
                    tenant=instance.tenant
                ).first()
                
                if stock_level and stock_level.cost_price:
                    cost_price = stock_level.cost_price
                else:
                    # Fallback to product cost if available
                    cost_price = getattr(line.product, 'cost_price', Decimal('0'))
                
                # Calculate COGS for this line
                line_cogs = line.quantity * cost_price
                total_cogs += line_cogs
                
            except Exception as e:
                print(f"[POS COGS] Error calculating COGS for {line.product}: {e}")
                continue
        
        # Only create entry if there's a COGS amount
        if total_cogs <= 0:
            return
        
        # Check if we need a separate COGS account integration
        # Try to get specific COGS integration, fallback to existing pos_sale config
        try:
            cogs_config = AccountingIntegration.objects.get(
                tenant=instance.tenant,
                event_type='inventory_loss'  # Temporarily use this for COGS
            )
            cogs_debit = cogs_config.debit_account  # COGS account
            inventory_credit = cogs_config.credit_account  # Inventory account
        except AccountingIntegration.DoesNotExist:
            # If no specific config, we can't create COGS entry
            print(f"[POS COGS] No accounting integration configured for COGS (Tenant: {instance.tenant})")
            return
        
        # Build journal entry lines for COGS
        lines = [
            {
                'account': cogs_debit,  # Cost of Goods Sold
                'debit': total_cogs,
                'credit': 0,
                'description': f"COGS for POS Sale {instance.transaction_number}"
            },
            {
                'account': inventory_credit,  # Inventory
                'debit': 0,
                'credit': total_cogs,
                'description': f"Inventory reduction for sale"
            }
        ]
        
        # Create separate COGS journal entry
        # Note: The revenue entry is created by accounting/signals.py
        JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.created_at.date(),
            description=f"COGS - POS Sale {instance.transaction_number}",
            user=instance.cashier,
            lines=lines,
            reference=f"COGS-{instance.transaction_number}",
            status='posted'
        )
        
    except AccountingIntegration.DoesNotExist:
        print(f"[POS COGS] No accounting integration configured for pos_sale (Tenant: {instance.tenant})")
    except Exception as e:
        print(f"[POS COGS] Error creating COGS entry for {instance.transaction_number}: {e}")
