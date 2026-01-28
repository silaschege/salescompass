from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Depreciation
from accounting.models import JournalEntry, JournalEntryLine
from django.db import transaction

@receiver(post_save, sender=Depreciation)
def create_depreciation_journal_entry(sender, instance, created, **kwargs):
    """
    Auto-generate Journal Entry for recorded depreciation.
    """
    if created and not instance.journal_entry:
        asset = instance.asset
        category = asset.category
        
        # Ensure we have required accounts
        if not all([category.depreciation_account, category.accumulated_depreciation_account]):
            return

        try:
            with transaction.atomic():
                # Create Journal Header
                journal = JournalEntry.objects.create(
                    tenant=instance.tenant,
                    entry_number=f"JE-DEP-{asset.asset_number}-{instance.date.strftime('%Y%m')}",
                    entry_date=instance.date,
                    description=f"Monthly Depreciation: {asset.name}",
                    reference=asset.asset_number,
                    status='posted'
                )
                
                # Debit Depreciation Expense
                JournalEntryLine.objects.create(
                    tenant=instance.tenant,
                    journal_entry=journal,
                    account=category.depreciation_account,
                    description=f"Depreciation Expense - {asset.name}",
                    debit=instance.amount,
                    credit=0
                )
                
                # Credit Accumulated Depreciation
                JournalEntryLine.objects.create(
                    tenant=instance.tenant,
                    journal_entry=journal,
                    account=category.accumulated_depreciation_account,
                    description=f"Accumulated Depreciation - {asset.name}",
                    debit=0,
                    credit=instance.amount
                )
                
                # Link back to depreciation record
                instance.journal_entry = journal
                # Update asset current value in the same transaction
                asset.current_value -= instance.amount
                asset.save()
                instance.save()
                
        except Exception as e:
            # Log error
            print(f"Error creating journal for depreciation {instance.id}: {e}")
