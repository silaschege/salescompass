from accounting.models import JournalEntry, JournalEntryLine, ChartOfAccount, TaxRate, TaxRule
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

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
    def post_invoice_to_gl(invoice):
        """
        Creates journal entry for a validated invoice.
        Dr Accounts Receivable
        Cr Sales Revenue
        """
        from accounting.services import JournalService
        from accounting.models import ChartOfAccount
        
        try:
            ar_account = ChartOfAccount.objects.filter(
                tenant=invoice.tenant, 
                account_type='asset',
                account_name__icontains='Receivable'
            ).first()
            
            sales_account = ChartOfAccount.objects.filter(
                tenant=invoice.tenant, 
                account_type='revenue',
                account_name__icontains='Sales'
            ).first()
            
            if not ar_account or not sales_account:
                logger.warning(f"Accounts for invoice posting not found for tenant {invoice.tenant}")
                return None

            lines = [
                {
                    'account': ar_account,
                    'debit': invoice.total_amount,
                    'credit': 0,
                    'description': f"Invoice {invoice.invoice_number}"
                },
                {
                    'account': sales_account,
                    'debit': 0,
                    'credit': invoice.total_amount,
                    'description': "Sales Revenue"
                }
            ]
            
            journal = JournalService.create_journal_entry(
                tenant=invoice.tenant,
                date=invoice.issue_date,
                description=f"Invoice Posting: {invoice.invoice_number}",
                user=None, # System or background task
                lines=lines,
                reference=invoice.invoice_number,
                status='posted'
            )
            return journal
        except Exception as e:
            logger.error(f"Error posting invoice {invoice.invoice_number} to GL: {e}")
            return None

    @staticmethod
    def post_payment_to_gl(payment):
        """
        Creates journal entry for a completed payment.
        Dr Cash/Bank
        Cr Accounts Receivable
        """
        from accounting.services import JournalService
        from accounting.models import ChartOfAccount
        
        try:
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

            lines = [
                {
                    'account': cash_account,
                    'debit': payment.amount,
                    'credit': 0,
                    'description': f"Payment {payment.payment_number}"
                },
                {
                    'account': ar_account,
                    'debit': 0,
                    'credit': payment.amount,
                    'description': f"Payment for {payment.invoice.invoice_number}"
                }
            ]
            
            journal = JournalService.create_journal_entry(
                tenant=payment.tenant,
                date=payment.payment_date,
                description=f"Payment Posting: {payment.payment_number}",
                user=None,
                lines=lines,
                reference=payment.payment_number,
                status='posted'
            )
            return journal
        except Exception as e:
            logger.error(f"Error posting payment {payment.payment_number} to GL: {e}")
            return None

class InvoiceService:
    @staticmethod
    def generate_pdf(invoice):
        """
        Generate PDF for a tenant invoice.
        """
        try:
            # In a real implementation:
            # from django.template.loader import render_to_string
            # from weasyprint import HTML
            # html = render_to_string('invoicing/invoice_pdf.html', {'invoice': invoice})
            # pdf = HTML(string=html).write_pdf()
            logger.info(f"Generating PDF for Invoice {invoice.invoice_number}")
            return f"/media/invoices/{invoice.invoice_number}.pdf"
        except Exception as e:
            logger.error(f"Error generating PDF for {invoice.invoice_number}: {e}")
            return None

    @staticmethod
    def send_to_customer(invoice):
        """
        Email the invoice to the customer.
        """
        try:
            # from django.core.mail import EmailMessage
            # email = EmailMessage(...)
            # email.attach_file(InvoiceService.generate_pdf(invoice))
            # email.send()
            logger.info(f"Sending Invoice {invoice.invoice_number} to {invoice.customer.email}")
            return True
        except Exception as e:
            logger.error(f"Error sending invoice {invoice.invoice_number}: {e}")
            return False

class InvoicingPaymentService:
    @staticmethod
    def record_payment(invoice, amount, method, payment_date=None, reference=''):
        """
        Record a payment from a customer.
        """
        from .models import Payment
        
        with transaction.atomic():
            payment = Payment.objects.create(
                tenant=invoice.tenant,
                invoice=invoice,
                amount=amount,
                payment_date=payment_date or timezone.now().date(),
                payment_method=method,
                reference_number=reference
            )
            
            invoice.amount_paid += amount
            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = 'paid'
            elif invoice.amount_paid > 0:
                invoice.status = 'partial'
                
            invoice.save()
            
            # Post to GL
            # AccountingIntegrationService.post_payment_to_gl(payment)
            
            return payment
