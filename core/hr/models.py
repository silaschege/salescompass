from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User, TimeStampedModel

EMPLOYMENT_TYPE_CHOICES = [
    ('full_time', 'Full Time'),
    ('part_time', 'Part Time'),
    ('contract', 'Contract'),
    ('intern', 'Intern'),
]

SALARY_TYPE_CHOICES = [
    ('hourly', 'Hourly'),
    ('monthly', 'Monthly'),
    ('annual', 'Annual'),
]

LEAVE_TYPE_CHOICES = [
    ('annual', 'Annual Leave'),
    ('sick', 'Sick Leave'),
    ('unpaid', 'Unpaid Leave'),
    ('maternity', 'Maternity/Paternity'),
]

LEAVE_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class Department(TenantModel, TimeStampedModel):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    cost_center = models.ForeignKey('accounting.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name

class Employee(TenantModel, TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100)
    
    hire_date = models.DateField()
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES, default='monthly')
    
    bank_account = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # IAS 19 Fields
    pension_scheme = models.CharField(max_length=100, blank=True, help_text="Standard Pension or Retirement plan")
    contract_end_date = models.DateField(null=True, blank=True, help_text="Required for termination benefit forecasting")
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

class Attendance(TenantModel, TimeStampedModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='present') # present, absent, leave
    
    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date}"

class LeaveRequest(TenantModel, TimeStampedModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.status})"

class PayrollRun(TenantModel, TimeStampedModel):
    """
    Groups payroll records for a period.
    """
    period_name = models.CharField(max_length=50) # e.g. "January 2025"
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('paid', 'Paid')], default='draft')
    
    total_gross = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    include_reimbursements = models.BooleanField(default=False, help_text="Search for and include approved expense reports in this payroll")
    
    # IAS 19 Compliance
    is_accrued = models.BooleanField(default=False, help_text="Recognized as expense in GL")
    accrual_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.period_name} ({self.status})"

class PayrollLine(TenantModel, TimeStampedModel):
    """
    Individual payroll record for an employee in a specific run.
    """
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='lines')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reimbursements = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Breakdown
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_withheld = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.employee} - {self.payroll_run.period_name}"
