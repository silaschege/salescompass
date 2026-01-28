from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from assets.models import FixedAsset
from accounting.models import JournalEntry, JournalEntryLine, ChartOfAccount
import uuid

class Command(BaseCommand):
    help = 'Processes monthly depreciation for all active assets and creates accounting journal entries.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        assets = FixedAsset.objects.filter(status='active')
        
        count = 0
        for asset in assets:
            if not asset.category.depreciation_account or not asset.category.accumulated_depreciation_account:
                self.stdout.write(self.style.WARNING(f"Skipping {asset.name}: No accounts configured in category."))
                continue

            # Calculate depreciation for this month (approximate if not yet calculated this month)
            # In a real system, we'd check a 'LastDepreciationDate' field.
            depr_amount = asset.calculate_depreciation(today)
            
            if depr_amount > 0:
                # Create Journal Entry
                journal = JournalEntry.objects.create(
                    entry_number=f"DEP-{uuid.uuid4().hex[:8].upper()}",
                    entry_date=today,
                    description=f"Monthly Depreciation for {asset.name} ({asset.asset_number})",
                    status='posted',
                    tenant=asset.tenant
                )
                
                # Debit Depreciation Expense
                JournalEntryLine.objects.create(
                    journal_entry=journal,
                    account=asset.category.depreciation_account,
                    description="Depreciation Expense",
                    debit=depr_amount,
                    tenant=asset.tenant
                )
                
                # Credit Accumulated Depreciation (Contra-Asset)
                JournalEntryLine.objects.create(
                    journal_entry=journal,
                    account=asset.category.accumulated_depreciation_account,
                    description="Accumulated Depreciation",
                    credit=depr_amount,
                    tenant=asset.tenant
                )
                
                # Update Asset Current Value
                asset.current_value = asset.purchase_cost - depr_amount # This logic is simplified
                asset.save()
                
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Depreciated {asset.name} by ${depr_amount}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {count} assets."))
