from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import FixedAsset, Depreciation, AssetImpairment, AssetRevaluation
from accounting.models import AccountingIntegration, ChartOfAccount, JournalEntry, JournalEntryLine

class AssetDepreciationService:
    """
    Handles complex depreciation calculations and periodic processing.
    """
    
    @staticmethod
    def calculate_period_depreciation(asset, target_date=None):
        """
        Calculates depreciation for a specific period based on method.
        """
        if target_date is None:
            target_date = timezone.now().date()
            
        # Implementation of methods like Straight Line, Declining Balance, Units of Production
        # (Leveraging existing logic but expanding for multi-method support)
        return asset.calculate_depreciation(target_date=target_date)

    @staticmethod
    @transaction.atomic
    def process_monthly_depreciation(tenant, user):
        """
        Batch process depreciation for all active assets for the current month.
        """
        today = timezone.now().date()
        assets = FixedAsset.objects.filter(tenant=tenant, status='active')
        
        runs = []
        for asset in assets:
            # Check if already depreciated this month
            if Depreciation.objects.filter(asset=asset, date__month=today.month, date__year=today.year).exists():
                continue
                
            amount = asset.calculate_depreciation(target_date=today)
            # We want only the DELTA if it's monthly
            # Simplified for now: assume last depreciation was last month
            last_dep = asset.depreciations.order_by('-date').first()
            if last_dep:
                total_cumulative = asset.calculate_depreciation(target_date=today)
                last_total = asset.calculate_depreciation(target_date=last_dep.date)
                amount = total_cumulative - last_total
            
            if amount > 0:
                dep_record = Depreciation.objects.create(
                    tenant=tenant,
                    asset=asset,
                    date=today,
                    amount=amount
                )
                runs.append(dep_record)
        return runs

class AssetAccountingService:
    """
    Integrates Asset events with the General Ledger.
    """
    
    @staticmethod
    @transaction.atomic
    def record_acquisition(asset, user):
        """
        Capitalize an asset purchase.
        Dr Asset (Cost)
        Cr Asset Payable / Bank
        """
        tenant = asset.tenant
        category = asset.category
        
        asset_account = category.asset_account
        # We need a payable/clearing account
        try:
            rule = AccountingIntegration.objects.get(tenant=tenant, event_type='asset_acquisition', is_active=True)
            payable_account = rule.credit_account # Or debit? Rule should define.
        except AccountingIntegration.DoesNotExist:
            payable_account = ChartOfAccount.objects.filter(tenant=tenant, account_type='liability_current', name__icontains='Payable').first()

        if not asset_account or not payable_account:
            return None

        # Create Journal Entry... (Simplified call to a helper or directly here)
        # Using the same pattern as HR but for assets.
        pass

    @staticmethod
    @transaction.atomic
    def record_impairment(asset, impairment_loss, reason, user):
        """
        Record IAS 36 Impairment.
        Dr Impairment Loss (Expense)
        Cr Accumulated Impairment/Asset
        """
        tenant = asset.tenant
        category = asset.category
        
        loss_account = category.impairment_account
        asset_account = category.asset_account # Or Accumulated Impairment
        
        if not loss_account or not asset_account:
            raise ValueError("Impairment accounts not configured for category.")

        impairment = AssetImpairment.objects.create(
            tenant=tenant,
            asset=asset,
            date=timezone.now().date(),
            impairment_loss=impairment_loss,
            reason=reason
        )
        
        # update asset carrying amount
        asset.accumulated_impairment += impairment_loss
        asset.current_value -= impairment_loss
        asset.save()
        
        # Post to GL logic here...
        return impairment

    @staticmethod
    @transaction.atomic
    def record_revaluation(asset, new_fair_value, user):
        """
        Record IAS 16 Revaluation Surplus.
        Dr Asset (Cost/Fair Value)
        Cr Revaluation Surplus (Equity)
        """
        tenant = asset.tenant
        category = asset.category
        
        adjustment = new_fair_value - asset.current_value
        surplus_account = category.revaluation_surplus_account
        asset_account = category.asset_account
        
        if not surplus_account or not asset_account:
            raise ValueError("Revaluation accounts not configured.")

        rev = AssetRevaluation.objects.create(
            tenant=tenant,
            asset=asset,
            date=timezone.now().date(),
            new_fair_value=new_fair_value,
            adjustment_amount=adjustment
        )
        
        asset.revaluation_surplus += adjustment
        asset.current_value = new_fair_value
        asset.save()
        
        # Post to GL logic here...
        return rev
