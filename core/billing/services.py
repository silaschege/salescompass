from accounting.models import JournalEntry, JournalEntryLine, ChartOfAccount, TaxRate, TaxRule
from django.db import transaction
from decimal import Decimal

class TaxService:
    @staticmethod
    def calculate_tax(price, product, tenant, region=None):
        """
        Calculate tax amount for a given price and product.
        Returns: (tax_amount, tax_rate_obj)
        """
        rate = TaxService.get_applicable_tax_rate(product, tenant, region)
        if not rate:
            return Decimal('0.00'), None
            
        tax_amount = price * (rate.rate / Decimal('100'))
        return tax_amount, rate

    @staticmethod
    def get_applicable_tax_rate(product, tenant, region=None):
        """
        Determine the correct tax rate based on precedence:
        1. Product Specific Override
        2. Regional/Category Tax Rules (High Priority)
        3. Default Tenant Tax Rate
        """
        # 1. Product Override
        if product.tax_rate:
            return product.tax_rate
            
        # 2. Tax Rules
        # Filter active rules for this tenant
        rules = TaxRule.objects.filter(tenant=tenant, is_active=True).order_by('-priority')
        
        # Apply filters
        for rule in rules:
            if rule.region and rule.region != region:
                continue
            if rule.product_category and rule.product_category != product.category:
                continue
            return rule.tax_rate
            
        # 3. Default
        try:
            return TaxRate.objects.get(tenant=tenant, is_default=True, is_active=True)
        except Exception:
             return TaxRate.objects.filter(tenant=tenant, is_default=True, is_active=True).first()

class AccountingIntegrationService:
    """
    Handles generation of Journal Entries from various business events.
    """
    
    @staticmethod
    def post_payment_to_gl(payment):
        """
        Creates journal entry for a completed payment.
        """
        if payment.status != 'completed':
            return None
            
        try:
            # Simplified Account Lookup
            cash_account = ChartOfAccount.objects.filter(
                tenant=payment.tenant, 
                account_type='asset',
                account_name__icontains='Bank'
            ).first() or ChartOfAccount.objects.filter(
                tenant=payment.tenant, 
                account_type='asset',
                account_name__icontains='Cash'
            ).first()
            
            ar_account = ChartOfAccount.objects.filter(
                tenant=payment.tenant, 
                account_type='asset',
                account_name__icontains='Receivable'
            ).first()
            
            if not cash_account or not ar_account:
                return None

            with transaction.atomic():
                journal = JournalEntry.objects.create(
                    tenant=payment.tenant,
                    entry_number=f"JE-PAY-{payment.payment_number}",
                    entry_date=payment.payment_date,
                    description=f"Payment for Invoice {payment.invoice.invoice_number}",
                    reference=payment.payment_number,
                    status='posted',
                    created_by=payment.recorded_by,
                    posted_by=payment.recorded_by,
                    posted_at=payment.created_at
                )
                
                # Debit Bank/Cash
                JournalEntryLine.objects.create(
                    tenant=payment.tenant,
                    journal_entry=journal,
                    account=cash_account,
                    description="Payment Received",
                    debit=payment.amount,
                    credit=0
                )
                
                # Credit Accounts Receivable
                JournalEntryLine.objects.create(
                    tenant=payment.tenant,
                    journal_entry=journal,
                    account=ar_account,
                    description="Invoice Payment",
                    debit=0,
                    credit=payment.amount
                )
                
                return journal
        except Exception as e:
            print(f"Error creating journal for payment {payment.payment_number}: {e}")
            return None

    @staticmethod
    def post_pos_sale_to_gl(transaction_obj):
        """
        Creates journal entry for a completed POS transaction.
        """
        if transaction_obj.status != 'completed':
            return None
            
        try:
            cash_account = ChartOfAccount.objects.filter(
                tenant=transaction_obj.tenant, 
                account_type='asset',
                account_name__icontains='Cash'
            ).first()
            
            sales_account = ChartOfAccount.objects.filter(
                tenant=transaction_obj.tenant, 
                account_type='revenue',
                account_name__icontains='Sales'
            ).first()
            
            if not cash_account or not sales_account:
                return None

            with transaction.atomic():
                journal = JournalEntry.objects.create(
                    tenant=transaction_obj.tenant,
                    entry_number=f"JE-POS-{transaction_obj.transaction_number}",
                    entry_date=transaction_obj.completed_at.date() if transaction_obj.completed_at else transaction_obj.created_at.date(),
                    description=f"POS Sale: {transaction_obj.transaction_number}",
                    reference=transaction_obj.transaction_number,
                    status='posted',
                    created_by=transaction_obj.cashier,
                    posted_by=transaction_obj.cashier,
                    posted_at=transaction_obj.completed_at or transaction_obj.created_at
                )
                
                # Debit Cash
                JournalEntryLine.objects.create(
                    tenant=transaction_obj.tenant,
                    journal_entry=journal,
                    account=cash_account,
                    description="Cash Sales",
                    debit=transaction_obj.total_amount,
                    credit=0
                )
                
                # Credit Revenue
                JournalEntryLine.objects.create(
                    tenant=transaction_obj.tenant,
                    journal_entry=journal,
                    account=sales_account,
                    description="Sales Revenue",
                    debit=0,
                    credit=transaction_obj.total_amount
                )
                
                return journal
        except Exception as e:
            print(f"Error creating journal for POS {transaction_obj.transaction_number}: {e}")
            return None
