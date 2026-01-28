from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Sale
from .models_contract import SalesContract, PerformanceObligation, RevenueSchedule
from accounting.models import JournalEntry, JournalEntryLine, AccountingIntegration
from inventory.services_valuation import ValuationService
from inventory.models import StockLevel

class RevenueRecognitionService:
    """
    Handles IFRS 15 Step 5: Recognizing revenue when performance obligations are satisfied.
    """

    @staticmethod
    @transaction.atomic
    def defer_on_sale(sale):
        """
        Record the initial liability (Contract Liability/Deferred Revenue) upon sale.
        Dr Cash/AR
        Cr Deferred Revenue
        """
        tenant = sale.tenant
        product = sale.product
        
        # Determine accounts from Category
        category = product.category
        deferred_acct = category.deferred_revenue_account if category else None
        
        if not deferred_acct:
            # Fallback to integration rule
            try:
                rule = AccountingIntegration.objects.get(tenant=tenant, event_type='revenue_deferral', is_active=True)
                deferred_acct = rule.credit_account
            except AccountingIntegration.DoesNotExist:
                return None

        # Create Journal Entry
        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_number=f"JE-REV-DEF-{sale.id}",
            entry_date=sale.sale_date.date(),
            description=f"Revenue Deferral for Sale #{sale.id}: {product.product_name}",
            status='posted'
        )
        
        # Placeholder for Credit (Deferred Revenue)
        JournalEntryLine.objects.create(
            tenant=tenant, journal_entry=entry,
            account=deferred_acct,
            credit=sale.amount, debit=0,
            description=f"Contract Liability - {product.product_name}"
        )
        
        # Debits are handled by the Invoice/POS payment logic usually, 
        # but for standalone recognition we simulate AR link if needed.
        return entry

    @staticmethod
    @transaction.atomic
    def recognize_fulfillment(obligation, amount, date=None):
        """
        Move revenue from Deferred to Earned.
        Dr Deferred Revenue
        Cr Earned Revenue
        """
        tenant = obligation.tenant
        date = date or timezone.now().date()
        
        deferred_acct = obligation.deferred_revenue_account
        revenue_acct = obligation.revenue_account
        
        if not deferred_acct or not revenue_acct:
            return None

        # --- IAS 2 / IFRS 15 MATCHING PRINCIPLE ---
        # 1. Calculate COGS for this fulfillment (if product is inventory-tracked)
        cogs_amount = Decimal('0')
        asset_acct = None
        cogs_acct = None
        
        # We assume the obligation name or a linked field specifies the product
        # For now, we try to find the product via the contract link
        product = getattr(obligation.contract, 'product', None) # Simplified mapping
        
        if product and product.track_inventory:
            category = product.category
            asset_acct = category.asset_account if category else None
            cogs_acct = category.cogs_account if category else None
            
            if asset_acct and cogs_acct:
                # Get cost based on valuation method
                method = product.valuation_method
                # We need a warehouse... for now we use the default
                from inventory.models import Warehouse
                warehouse = Warehouse.objects.filter(tenant=tenant, is_default=True).first()
                
                if warehouse:
                    unit_cost = ValuationService.get_unit_cost(product, warehouse, method=method)
                    # Amount is revenue; we need quantity. 
                    # Assuming obligation has a quantity field or we derive it
                    qty = obligation.quantity if hasattr(obligation, 'quantity') else 1
                    cogs_amount = unit_cost * Decimal(qty)

        # 2. Create Schedule record
        schedule = RevenueSchedule.objects.create(
            tenant=tenant,
            obligation=obligation,
            date=date,
            amount=amount,
            is_recognized=True
        )

        entry = JournalEntry.objects.create(
            tenant=tenant,
            entry_number=f"JE-REV-REC-{schedule.id}",
            entry_date=date,
            description=f"Revenue Recognition: {obligation.name}",
            status='posted'
        )

        # Dr Deferred
        JournalEntryLine.objects.create(
            tenant=tenant, journal_entry=entry,
            account=deferred_acct,
            debit=amount, credit=0,
            description=f"Release of Deferral - {obligation.name}"
        )
        
        # Cr Revenue
        JournalEntryLine.objects.create(
            tenant=tenant, journal_entry=entry,
            account=revenue_acct,
            credit=amount, debit=0,
            description=f"Earned Revenue - {obligation.name}"
        )

        # --- COGS ENTRY (Matching Principle) ---
        if cogs_amount > 0 and asset_acct and cogs_acct:
            # Dr COGS
            JournalEntryLine.objects.create(
                tenant=tenant, journal_entry=entry,
                account=cogs_acct,
                debit=cogs_amount, credit=0,
                description=f"COGS Matching - {obligation.name}"
            )
            # Cr Inventory
            JournalEntryLine.objects.create(
                tenant=tenant, journal_entry=entry,
                account=asset_acct,
                credit=cogs_amount, debit=0,
                description=f"Inventory Reduction - {obligation.name}"
            )

        schedule.journal_entry = entry
        schedule.save()
        
        # Update obligation status
        obligation.recognized_amount += amount
        if obligation.recognized_amount >= obligation.allocated_amount:
            obligation.status = 'fulfilled'
        else:
            obligation.status = 'partially_fulfilled'
        obligation.save()
        
        return schedule

    @staticmethod
    @transaction.atomic
    def process_over_time_recognition(tenant):
        """
        Batch process revenue recognition for obligations that earn 'Over Time'.
        """
        today = timezone.now().date()
        obligations = PerformanceObligation.objects.filter(
            tenant=tenant,
            recognition_method='over_time',
            status__in=['unfulfilled', 'partially_fulfilled'],
            start_date__lte=today,
            end_date__gte=today
        )
        
        runs = []
        for ob in obligations:
            # Simple straight-line calculation
            total_days = (ob.end_date - ob.start_date).days + 1
            if total_days <= 0: continue
            
            daily_rate = ob.allocated_amount / total_days
            # Amount to recognize for today (if not already recognized)
            # In a real system, we'd check if today's portion is already in RevenueSchedule
            if not ob.schedules.filter(date=today).exists():
                res = RevenueRecognitionService.recognize_fulfillment(ob, daily_rate, date=today)
                if res: runs.append(res)
        
        return runs
