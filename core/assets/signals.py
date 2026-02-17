from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import (
    Depreciation, FixedAsset, AssetDisposal,
    AssetImpairment, AssetRevaluation
)
from accounting.services import JournalService
from accounting.models import AccountingIntegration
from decimal import Decimal


# ============================================================================
# ASSET DEPRECIATION INTEGRATION
# ============================================================================

@receiver(post_save, sender=Depreciation)
def handle_depreciation_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when depreciation is recorded.
    
    Accounting Entry:
    Dr: Depreciation Expense Account
    Cr: Accumulated Depreciation Account
    """
    # Only process new depreciation records
    if not created:
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='asset_depreciation'
        )
        
        # Try to use category-specific accounts if available
        debit_account = config.debit_account  # Depreciation Expense
        credit_account = config.credit_account  # Accumulated Depreciation
        
        # Override with asset category accounts if defined
        if instance.asset.category:
            if instance.asset.category.depreciation_account:
                debit_account = instance.asset.category.depreciation_account
            if instance.asset.category.accumulated_depreciation_account:
                credit_account = instance.asset.category.accumulated_depreciation_account
        
        # Build journal entry lines
        lines = [
            {
                'account': debit_account,
                'debit': instance.amount,
                'credit': 0,
                'description': f"Depreciation: {instance.asset.name}"
            },
            {
                'account': credit_account,
                'debit': 0,
                'credit': instance.amount,
                'description': f"Accumulated Depreciation: {instance.asset.asset_number}"
            }
        ]
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.date,
            description=f"Depreciation - {instance.asset.name}",
            user=None,  # System-generated
            lines=lines,
            reference=f"DEP-{instance.asset.asset_number}-{instance.date}",
            status='posted'
        )
        
        # Link journal entry
        instance.journal_entry = journal_entry
        instance._skip_signal = True
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for asset_depreciation (Tenant: {instance.tenant})")


# ============================================================================
# ASSET ACQUISITION INTEGRATION
# ============================================================================

@receiver(post_save, sender=FixedAsset)
def handle_asset_acquisition_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when a fixed asset is acquired.
    
    Accounting Entry:
    Dr: Fixed Asset Account
    Cr: Cash/Bank or Accounts Payable
    
    Note: This creates the capitalization entry when asset is first recorded.
    """
    # Only process new assets
    if not created:
        return
    
    # Skip if this is a component (already handled by parent)
    if instance.component_of:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='asset_acquisition'
        )
        
        # Use category-specific asset account if available
        asset_account = config.debit_account
        if instance.category and instance.category.asset_account:
            asset_account = instance.category.asset_account
        
        # Build journal entry lines
        lines = [
            {
                'account': asset_account,
                'debit': instance.purchase_cost,
                'credit': 0,
                'description': f"Asset Acquisition: {instance.name}"
            },
            {
                'account': config.credit_account,  # Cash or AP
                'debit': 0,
                'credit': instance.purchase_cost,
                'description': f"Payment for {instance.asset_number}"
            }
        ]
        
        # Create journal entry
        JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.purchase_date,
            description=f"Asset Capitalization: {instance.name}",
            user=None,
            lines=lines,
            reference=instance.asset_number,
            status='posted'
        )
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for asset_acquisition (Tenant: {instance.tenant})")


# ============================================================================
# ASSET DISPOSAL INTEGRATION
# ============================================================================

@receiver(post_save, sender=AssetDisposal)
def handle_asset_disposal_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when asset is disposed.
    
    Multi-line Accounting Entry:
    Dr: Cash (disposal proceeds)
    Dr: Accumulated Depreciation
    Dr/Cr: Gain/Loss on Disposal (balancing figure)
    Cr: Fixed Asset Account (original cost)
    """
    # Only process new disposals
    if not created:
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='asset_disposal'
        )
        
        # Determine accounts
        asset_account = config.credit_account  # Asset account (to be credited)
        if instance.asset.category and instance.asset.category.asset_account:
            asset_account = instance.asset.category.asset_account
        
        accumulated_dep_account = config.debit_account  # Accumulated Depreciation
        if instance.asset.category and instance.asset.category.accumulated_depreciation_account:
            accumulated_dep_account = instance.asset.category.accumulated_depreciation_account
        
        # Build multi-line journal entry
        lines = []
        
        # 1. Cash received (if any)
        if instance.disposal_proceeds > 0:
            lines.append({
                'account': config.debit_account,  # Assume this is cash/bank
                'debit': instance.disposal_proceeds,
                'credit': 0,
                'description': f"Proceeds from disposal of {instance.asset.name}"
            })
        
        # 2. Accumulated Depreciation (debit to remove)
        lines.append({
            'account': accumulated_dep_account,
            'debit': instance.accumulated_depreciation_at_disposal,
            'credit': 0,
            'description': f"Accumulated Depreciation removal: {instance.asset.asset_number}"
        })
        
        # 3. Gain or Loss (balancing entry)
        if instance.gain_loss != 0:
            if instance.gain_loss > 0:
                # Gain on disposal (credit)
                lines.append({
                    'account': config.credit_account,  # Gain account
                    'debit': 0,
                    'credit': abs(instance.gain_loss),
                    'description': f"Gain on disposal: {instance.asset.name}"
                })
            else:
                # Loss on disposal (debit)
                lines.append({
                    'account': config.debit_account,  # Loss account
                    'debit': abs(instance.gain_loss),
                    'credit': 0,
                    'description': f"Loss on disposal: {instance.asset.name}"
                })
        
        # 4. Original Asset Cost (credit to remove)
        lines.append({
            'account': asset_account,
            'debit': 0,
            'credit': instance.cost_at_disposal,
            'description': f"Asset disposal: {instance.asset.asset_number}"
        })
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.disposal_date,
            description=f"Asset Disposal: {instance.asset.name}",
            user=None,
            lines=lines,
            reference=f"DISP-{instance.asset.asset_number}",
            status='posted'
        )
        
        # Link journal entry
        instance.journal_entry = journal_entry
        instance._skip_signal = True
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for asset_disposal (Tenant: {instance.tenant})")


# ============================================================================
# ASSET IMPAIRMENT INTEGRATION (IAS 36)
# ============================================================================

@receiver(post_save, sender=AssetImpairment)
def handle_asset_impairment_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when asset impairment is recorded.
    
    Accounting Entry:
    Dr: Impairment Loss (Expense)
    Cr: Accumulated Impairment or Asset Account
    """
    # Only process new impairments
    if not created:
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='asset_impairment'
        )
        
        # Use category-specific impairment account if available
        impairment_expense = config.debit_account
        accumulated_impairment = config.credit_account
        
        if instance.asset.category and instance.asset.category.impairment_account:
            impairment_expense = instance.asset.category.impairment_account
        
        # Build journal entry lines
        lines = [
            {
                'account': impairment_expense,
                'debit': instance.impairment_loss,
                'credit': 0,
                'description': f"Impairment Loss: {instance.asset.name}"
            },
            {
                'account': accumulated_impairment,
                'debit': 0,
                'credit': instance.impairment_loss,
                'description': f"Accumulated Impairment: {instance.asset.asset_number}"
            }
        ]
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.date,
            description=f"Asset Impairment: {instance.asset.name} - {instance.reason}",
            user=None,
            lines=lines,
            reference=f"IMP-{instance.asset.asset_number}-{instance.date}",
            status='posted'
        )
        
        # Link journal entry
        instance.journal_entry = journal_entry
        instance._skip_signal = True
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for asset_impairment (Tenant: {instance.tenant})")


# ============================================================================
# ASSET REVALUATION INTEGRATION (IAS 16)
# ============================================================================

@receiver(post_save, sender=AssetRevaluation)
def handle_asset_revaluation_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when asset is revalued.
    
    For Revaluation Surplus (increase):
    Dr: Fixed Asset Account
    Cr: Revaluation Surplus (Equity)
    
    For Revaluation Loss (decrease):
    Dr: Revaluation Loss (Expense)
    Cr: Fixed Asset Account
    """
    # Only process new revaluations
    if not created:
        return
    
    # Prevent duplicate entries
    if instance.journal_entry is not None:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='asset_revaluation'
        )
        
        # Use category-specific accounts if available
        asset_account = config.debit_account
        if instance.asset.category and instance.asset.category.asset_account:
            asset_account = instance.asset.category.asset_account
        
        revaluation_surplus_account = config.credit_account
        if instance.asset.category and instance.asset.category.revaluation_surplus_account:
            revaluation_surplus_account = instance.asset.category.revaluation_surplus_account
        
        # Determine if surplus or loss
        is_surplus = instance.adjustment_amount > 0
        
        if is_surplus:
            # Revaluation Surplus
            lines = [
                {
                    'account': asset_account,
                    'debit': abs(instance.adjustment_amount),
                    'credit': 0,
                    'description': f"Revaluation Surplus: {instance.asset.name}"
                },
                {
                    'account': revaluation_surplus_account,  # Equity
                    'debit': 0,
                    'credit': abs(instance.adjustment_amount),
                    'description': f"Revaluation Surplus - Fair Value Adjustment"
                }
            ]
        else:
            # Revaluation Loss
            lines = [
                {
                    'account': config.debit_account,  # Expense account
                    'debit': abs(instance.adjustment_amount),
                    'credit': 0,
                    'description': f"Revaluation Loss: {instance.asset.name}"
                },
                {
                    'account': asset_account,
                    'debit': 0,
                    'credit': abs(instance.adjustment_amount),
                    'description': f"Asset writedown to fair value"
                }
            ]
        
        # Create journal entry
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.date,
            description=f"Asset Revaluation: {instance.asset.name} to {instance.new_fair_value}",
            user=None,
            lines=lines,
            reference=f"REVAL-{instance.asset.asset_number}-{instance.date}",
            status='posted'
        )
        
        # Link journal entry
        instance.journal_entry = journal_entry
        instance._skip_signal = True
        instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for asset_revaluation (Tenant: {instance.tenant})")
