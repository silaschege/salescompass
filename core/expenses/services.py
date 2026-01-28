from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from accounting.models import AccountingIntegration, ChartOfAccount
from accounting.services import JournalService
from assets.models import FixedAsset, AssetCategory
from .models import ExpenseReport, ExpenseLine

class ExpenseAccountingService:
    """
    Service to handle IFRS/IPSAS compliant accounting for expenses.
    """

    @staticmethod
    @transaction.atomic
    def post_accrual(report, user):
        """
        Recognize expense accrual upon approval.
        Dr Expense (from Category)
        Cr Accrued Liability (Accruals)
        """
        if report.is_accrued:
            return None

        tenant = report.tenant
        lines_to_post = []
        
        # Get integration rule for accrual
        try:
            accrual_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='expense_accrual',
                is_active=True
            )
            liability_account = accrual_rule.credit_account
        except AccountingIntegration.DoesNotExist:
            # Fallback: Find a "Payables" or "Accrued" account
            liability_account = ChartOfAccount.objects.filter(
                tenant=tenant,
                account_type='liability_current',
                account_name__icontains='Accrued'
            ).first()

        if not liability_account:
             raise ValueError("No accrual liability account configured for expenses.")

        # Aggregate report lines by their category's GL account
        journal_lines = []
        total_amount = Decimal('0.00')

        for line in report.lines.all():
            expense_account = line.category.gl_account
            if not expense_account:
                continue
                
            journal_lines.append({
                'account': expense_account,
                'debit': line.amount - line.tax_amount,
                'credit': Decimal('0.00'),
                'description': f"Exp: {line.description} (Report {report.report_number})"
            })
            
            # Handle Tax (VAT) portion if any
            if line.tax_amount > 0:
                # Find Tax account... assuming a generic current asset/liability for now
                # Or a specific tax integration? 
                pass # Logic for tax splitting could go here

            total_amount += line.amount

            # Trigger CAPEX conversion if needed
            if line.is_capex:
                 ExpenseAccountingService.convert_to_asset(line, user)

        if not journal_lines:
            return None

        # Add the Credit leg
        journal_lines.append({
            'account': liability_account,
            'debit': Decimal('0.00'),
            'credit': total_amount,
            'description': f"Accrual for Expense Report {report.report_number}"
        })

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Accrual for Expense Report: {report.title}",
            user=user,
            lines=journal_lines,
            reference=report.report_number,
            status='posted',
            related_object=report
        )
        
        report.is_accrued = True
        report.save()
        return journal

    @staticmethod
    @transaction.atomic
    def post_payment(report, user):
        """
        Recognize payment/reimbursement.
        Dr Accrued Liability
        Cr Cash/Bank
        """
        tenant = report.tenant
        
        # Get integration rule for payment
        try:
            payment_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='expense_payment',
                is_active=True
            )
            bank_account = payment_rule.credit_account # Usually CR Bank/Cash
            liability_account = payment_rule.debit_account # Usually DR Accrued Liability
        except AccountingIntegration.DoesNotExist:
             raise ValueError("No payment integration rule configured for expenses.")

        journal_lines = [
            {
                'account': liability_account,
                'debit': report.total_amount,
                'credit': Decimal('0.00'),
                'description': f"Payment Settlement (Report {report.report_number})"
            },
            {
                'account': bank_account,
                'debit': Decimal('0.00'),
                'credit': report.total_amount,
                'description': f"Payment Settlement (Report {report.report_number})"
            }
        ]

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Payment/Reimbursement for Expense Report: {report.title}",
            user=user,
            lines=journal_lines,
            reference=report.report_number,
            status='posted',
            related_object=report
        )
        
        return journal

    @staticmethod
    def convert_to_asset(line, user):
        """
        Converts a CAPEX expense line to a FixedAsset.
        """
        # Find or create a matching asset category
        asset_cat = AssetCategory.objects.filter(tenant=line.tenant, name=line.category.name).first()
        if not asset_cat:
            # Fallback to first available or create general
            asset_cat = AssetCategory.objects.filter(tenant=line.tenant).first()
            
        if not asset_cat:
            return None # No asset categories setup
            
        import uuid
        asset = FixedAsset.objects.create(
            tenant=line.tenant,
            asset_number=f"AST-{uuid.uuid4().hex[:8].upper()}",
            name=line.description,
            category=asset_cat,
            purchase_date=line.date,
            purchase_cost=line.amount,
            status='active',
            assigned_to=line.report.employee
        )
        
        line.related_asset = asset
        line.save()
        return asset
