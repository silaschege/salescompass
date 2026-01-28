from decimal import Decimal
from django.db import transaction, models
from django.db.models import Sum
from django.utils import timezone
from .models import PayrollRun, PayrollLine, Employee
from expenses.models import ExpenseReport
from commissions.models import Commission
from accounting.models import AccountingIntegration, ChartOfAccount
from accounting.services import JournalService

class PayrollIntegrationService:
    """
    Handles complex logic for payroll runs, including commission extraction,
    expense reconciliation, and IAS 19 compliant accounting.
    """
    
    @staticmethod
    @transaction.atomic
    def generate_payroll_lines(payroll_run):
        """
        Populates payroll lines for all active employees.
        Integrates commissions and base salary.
        """
        employees = Employee.objects.filter(tenant=payroll_run.tenant, is_active=True)
        
        for emp in employees:
            # 1. Base Salary
            gross = emp.salary
            
            # 2. Extract Approved Commissions for the period
            # Logic: commissions earned in the month prior to payment date (usually)
            # Or based on payroll_run period name if parsed
            commissions = Commission.objects.filter(
                tenant=payroll_run.tenant,
                user=emp.user,
                status='approved',
                payment_record__isnull=True # Not yet paid
            )
            total_commissions = commissions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            # 3. Create or Update line
            line, created = PayrollLine.objects.update_or_create(
                payroll_run=payroll_run,
                employee=emp,
                defaults={
                    'gross_salary': gross,
                    'commission_amount': total_commissions,
                    'net_salary': gross + total_commissions, # Simplified for now
                    'tenant': payroll_run.tenant
                }
            )
            
            # Mark commissions as "Included" (ideally link them)
            # commissions.update(status='paid') # Handled during final settlement

    @staticmethod
    def reconcile_expenses(payroll_run):
        """
        Finds approved expense reports for employees and links them to the payroll run.
        """
        for line in payroll_run.lines.all():
            reports = ExpenseReport.objects.filter(
                tenant=payroll_run.tenant,
                employee=line.employee.user,
                status='approved',
                payroll_run__isnull=True
            )
            
            total_reimbursement = Decimal('0.00')
            for report in reports:
                report.payroll_run = payroll_run
                report.save()
                total_reimbursement += report.total_amount
            
            line.reimbursements = total_reimbursement
            # Update net salary
            line.net_salary = line.gross_salary + line.commission_amount - line.deductions + line.reimbursements
            line.save()
            
        payroll_run.total_net = sum(l.net_salary for l in payroll_run.lines.all())
        payroll_run.save()

    @staticmethod
    @transaction.atomic
    def post_accrual(payroll_run, user):
        """
        Recognize payroll expense and liability (Accrual step).
        Dr Salary Expense
        Cr Salaries Payable
        """
        if payroll_run.is_accrued:
            return None

        tenant = payroll_run.tenant
        
        try:
            accrual_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='payroll_accrual',
                is_active=True
            )
            expense_account = accrual_rule.debit_account
            payable_account = accrual_rule.credit_account
        except AccountingIntegration.DoesNotExist:
            # Fallback
            expense_account = ChartOfAccount.objects.filter(tenant=tenant, account_type='expense', account_name__icontains='Salary').first()
            payable_account = ChartOfAccount.objects.filter(tenant=tenant, account_type='liability_current', account_name__icontains='Payable').first()

        if not expense_account or not payable_account:
            raise ValueError("Accounting rules for payroll accrual not configured.")

        journal_lines = [
            {
                'account': expense_account,
                'debit': payroll_run.total_gross,
                'credit': Decimal('0.00'),
                'description': f"Payroll Accrual - {payroll_run.period_name}"
            },
            {
                'account': payable_account,
                'debit': Decimal('0.00'),
                'credit': payroll_run.total_gross,
                'description': f"Payroll Liability - {payroll_run.period_name}"
            }
        ]

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Accrual for Payroll: {payroll_run.period_name}",
            user=user,
            lines=journal_lines,
            reference=f"PAY-{payroll_run.id}",
            status='posted',
            related_object=payroll_run
        )
        
        payroll_run.is_accrued = True
        payroll_run.accrual_date = timezone.now().date()
        payroll_run.save()
        return journal

    @staticmethod
    @transaction.atomic
    def post_settlement(payroll_run, user):
        """
        Recognize actual payment of salaries.
        Dr Salaries Payable
        Cr Bank/Cash
        """
        tenant = payroll_run.tenant
        
        try:
            payment_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='payroll_payment',
                is_active=True
            )
            payable_account = payment_rule.debit_account
            bank_account = payment_rule.credit_account
        except AccountingIntegration.DoesNotExist:
            payable_account = ChartOfAccount.objects.filter(tenant=tenant, account_type='liability_current', account_name__icontains='Payable').first()
            bank_account = ChartOfAccount.objects.filter(tenant=tenant, is_bank_account=True).first()

        journal_lines = [
            {
                'account': payable_account,
                'debit': payroll_run.total_net,
                'credit': Decimal('0.00'),
                'description': f"Payroll Settlement - {payroll_run.period_name}"
            },
            {
                'account': bank_account,
                'debit': Decimal('0.00'),
                'credit': payroll_run.total_net,
                'description': f"Bank Payment - {payroll_run.period_name}"
            }
        ]

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Settlement for Payroll: {payroll_run.period_name}",
            user=user,
            lines=journal_lines,
            reference=f"PAY-SET-{payroll_run.id}",
            status='posted',
            related_object=payroll_run
        )
        
        payroll_run.status = 'paid'
        payroll_run.payment_date = timezone.now().date()
        payroll_run.save()
        return journal
