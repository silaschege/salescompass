from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from hr.models import Employee
from learn.models import UserProgress, Course
from .services import EmployeeService

@receiver(pre_save, sender=Employee)
def validate_employee_certification(sender, instance, **kwargs):
    """
    Example safety check: Before promoting an employee to 'Warehouse Lead',
    verify they have completed the 'Warehouse Safety 101' course in Learn.
    """
    # Note: job_title was changed to position in models.py, updating here for consistency
    if hasattr(instance, 'position') and instance.position == 'Warehouse Lead':
        safety_course = Course.objects.filter(title__icontains='Warehouse Safety').first()
        if safety_course:
            progress = UserProgress.objects.filter(
                user=instance.user,
                course=safety_course,
                completion_status='completed'
            ).exists()
            
            if not progress:
                # In a real system, we might just log a warning or send an alert.
                # For this ERP prototype, we'll demonstrate a 'soft' validation notice.
                print(f"WARNING: Employee {instance.user.email} is missing mandatory certification: {safety_course.title}")
                # instance.compliance_alert = True (if field existed)

@receiver(post_save, sender=Employee)
def link_employee_to_tenant_member(sender, instance, created, **kwargs):
    """
    Automatically link the employee to a TenantMember on creation 
    and maintain consistency on updates.
    """
    if created or not instance.tenant_member:
        EmployeeService.sync_tenant_member(instance)
    
    # Optional: ensure consistency of status/fields
    # We call this on every save to keep them in sync
    EmployeeService.ensure_consistency(instance)


# ============================================================================
# PAYROLL ACCOUNTING INTEGRATION
# ============================================================================

from accounting.services import JournalService
from accounting.models import AccountingIntegration
from decimal import Decimal
from django.db import transaction as db_transaction

@receiver(post_save, sender='hr.PayrollRun')
def handle_payroll_accrual_save(sender, instance, created, **kwargs):
    """
    Trigger journal entry when payroll is accrued (IAS 19).
    
    Dr: Salary Expense, Cr: Salaries Payable + Tax Withholding Payable
    """
    if not instance.is_accrued or instance.status != 'finalized':
        return
    
    if hasattr(instance, 'journal_entry') and instance.journal_entry:
        return
    
    try:
        config = AccountingIntegration.objects.get(
            tenant=instance.tenant,
            event_type='payroll_accrual'
        )
        
        total_gross_pay = sum(line.gross_pay for line in instance.lines.all())
        total_deductions = sum(line.total_deductions for line in instance.lines.all())
        total_net_pay = sum(line.net_pay for line in instance.lines.all())
        
        lines = [
            {
                'account': config.debit_account,
                'debit': total_gross_pay,
                'credit': 0,
                'description': f"Payroll Expense: {instance.pay_period_start} to {instance.pay_period_end}"
            },
            {
                'account': config.credit_account,
                'debit': 0,
                'credit': total_net_pay,
                'description': f"Salaries Payable: {instance.lines.count()} employees"
            }
        ]
        
        if total_deductions > 0:
            lines.append({
                'account': config.credit_account,
                'debit': 0,
                'credit': total_deductions,
                'description': f"Tax Withholdings & Deductions"
            })
        
        journal_entry = JournalService.create_journal_entry(
            tenant=instance.tenant,
            date=instance.accrual_date if instance.accrual_date else instance.pay_date,
            description=f"Payroll Accrual: {instance.pay_period_start} to {instance.pay_period_end}",
            user=None,
            lines=lines,
            reference=f"PAYROLL-{instance.pk}",
            status='posted'
        )
        
        if hasattr(instance, 'journal_entry'):
            instance.journal_entry = journal_entry
            instance._skip_signal = True
            instance.save(update_fields=['journal_entry'])
        
    except AccountingIntegration.DoesNotExist:
        print(f"[Accounting] No integration configured for payroll_accrual (Tenant: {instance.tenant})")

