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


class EmployeeService:
    """
    Handles high-level operations for employees, ensuring integration with TenantMember.
    """
    
    @staticmethod
    def sync_tenant_member(employee):
        """
        Ensures the employee is linked to a corresponding TenantMember.
        If one exists with the same user and tenant, it links it.
        """
        from tenants.models import TenantMember
        
        member = TenantMember.objects.filter(
            user=employee.user,
            tenant=employee.tenant
        ).first()
        
        if member and employee.tenant_member != member:
            employee.tenant_member = member
            employee.save(update_fields=['tenant_member'])
        
        return employee

    @staticmethod
    @transaction.atomic
    def create_employee(user, tenant, data):
        """
        Creates an Employee record and ensures it's linked to a TenantMember.
        """
        # Ensure TenantMember exists or is accessible
        from tenants.models import TenantMember
        
        member, _ = TenantMember.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={'status': 'active'}
        )
        
        employee = Employee.objects.create(
            user=user,
            tenant=tenant,
            tenant_member=member,
            **data
        )
        
        return employee

    @staticmethod
    def ensure_consistency(employee):
        """
        Synchronizes fields between Employee and its linked TenantMember.
        """
        if not employee.tenant_member:
            EmployeeService.sync_tenant_member(employee)
            
        member = employee.tenant_member
        if not member:
            return
            
        # Example sync: if employee is inactive, set member status to terminated/inactive
        if not employee.is_active and member.status != 'terminated':
            member.status = 'terminated'
            member.termination_date = timezone.now().date()
            member.save(update_fields=['status', 'termination_date'])
        elif employee.is_active and member.status == 'terminated':
            member.status = 'active'
            member.save(update_fields=['status'])

class LeaveService:
    """
    Handles leave balance calculations and updates.
    """
    
    @staticmethod
    def get_requested_days(start_date, end_date):
        """
        Calculates the number of days between two dates (inclusive).
        """
        delta = end_date - start_date
        return delta.days + 1

    @staticmethod
    def check_balance(employee, leave_type, days):
        """
        Checks if an employee has sufficient balance for the requested leave.
        """
        from .models import LeaveBalance
        year = timezone.now().year
        balance = LeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=year
        ).first()
        
        if not balance:
            # If no balance record exists, we might assume 0 or handle initialization
            return False, "No leave balance record found for this year."
            
        if balance.remaining_days < Decimal(str(days)):
            return False, f"Insufficient balance. Available: {balance.remaining_days} days."
            
        return True, None

    @staticmethod
    @transaction.atomic
    def deduct_balance(leave_request):
        """
        Deducts the leave days from the employee's balance upon approval.
        """
        from .models import LeaveBalance
        
        if leave_request.status != 'approved':
            return
            
        days = LeaveService.get_requested_days(leave_request.start_date, leave_request.end_date)
        year = leave_request.start_date.year
        
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=year,
            defaults={'tenant': leave_request.tenant}
        )
        
        balance.used_days += Decimal(str(days))
        balance.save()
        
        return balance

class LeaveAccrualService:
    """
    Automates the process of adding leave entitlements to employee balances.
    Supports IAS 19 compliant accounting triggers.
    """
    
    @staticmethod
    @transaction.atomic
    def run_accruals(tenant, user=None):
        """
        Main entry point for periodic accruals.
        Usually triggered by a management command or cron job.
        """
        from .models import LeavePolicy, Employee, LeaveBalance
        from decimal import Decimal
        
        policies = LeavePolicy.objects.filter(tenant=tenant, is_active=True)
        employees = Employee.objects.filter(tenant=tenant, is_active=True)
        year = timezone.now().year
        
        accrual_results = []
        total_accrued_value = Decimal('0.00')

        for policy in policies:
            # Determine accrual rate
            if policy.accrual_frequency == 'monthly':
                rate = policy.annual_entitlement / Decimal('12.0')
            else:
                # Annual lump sum (usually at start of year) - simplified logic
                rate = policy.annual_entitlement

            for emp in employees:
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=emp,
                    leave_type=policy.leave_type,
                    year=year,
                    defaults={'tenant': tenant}
                )
                
                balance.entitled_days += rate
                balance.save()
                
                # For accounting, we need a daily rate (Base Salary / 365 or 260)
                # Simplified: assume 260 working days
                daily_rate = emp.salary / Decimal('260.0')
                accrued_value = (rate * daily_rate).quantize(Decimal('0.01'))
                total_accrued_value += accrued_value
                
                accrual_results.append({
                    'employee': emp,
                    'leave_type': policy.leave_type,
                    'days': rate,
                    'value': accrued_value
                })

        # --- Accounting Integration (IAS 19 Provision) ---
        if total_accrued_value > 0:
            LeaveAccrualService._post_accounting_provision(tenant, total_accrued_value, user)

        return accrual_results

    @staticmethod
    def _post_accounting_provision(tenant, amount, user):
        """
        Posts a journal entry for the leave liability provision.
        Dr Leave Expense
        Cr Accrued Leave Liability
        """
        from accounting.models import AccountingIntegration, ChartOfAccount
        from accounting.services import JournalService
        
        try:
            rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='leave_accrual',
                is_active=True
            )
            debit_acc = rule.debit_account
            credit_acc = rule.credit_account
        except AccountingIntegration.DoesNotExist:
            # Fallback accounts
            debit_acc = ChartOfAccount.objects.filter(tenant=tenant, account_type='expense', account_name__icontains='Leave').first()
            credit_acc = ChartOfAccount.objects.filter(tenant=tenant, account_type='liability_current', account_name__icontains='Leave').first()

        if not debit_acc or not credit_acc:
            # Log failure but don't break the accrual process
            print(f"Accounting provision skipped: No rules found for leave_accrual in tenant {tenant}")
            return

        journal_lines = [
            {
                'account': debit_acc,
                'debit': amount,
                'credit': Decimal('0.00'),
                'description': f"Monthly Leave Accrual Provision - {timezone.now().strftime('%B %Y')}"
            },
            {
                'account': credit_acc,
                'debit': Decimal('0.00'),
                'credit': amount,
                'description': f"Leave Liability Increase - {timezone.now().strftime('%B %Y')}"
            }
        ]

        JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"IAS 19 Leave Provision - {timezone.now().strftime('%B %Y')}",
            user=user if user and not user.is_anonymous else None,
            lines=journal_lines,
            reference="LV-ACCRUAL",
            status='posted'
        )
