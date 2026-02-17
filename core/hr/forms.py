from django import forms
from .models import Employee, LeaveRequest, Department, PayrollRun
from core.models import User

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'user', 'employee_id', 'department', 'position', 
            'hire_date', 'contract_end_date', 'employment_type', 
            'salary', 'salary_type', 'pension_scheme', 'tenant_member'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            # Filter users in the tenant
            self.fields['user'].queryset = User.objects.filter(tenant=tenant)
            self.fields['department'].queryset = Department.objects.filter(tenant=tenant)
            from tenants.models import TenantMember
            self.fields['tenant_member'].queryset = TenantMember.objects.filter(tenant=tenant)

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'manager', 'cost_center']
    
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['manager'].queryset = Employee.objects.filter(tenant=tenant)
            from accounting.models import ChartOfAccount
            self.fields['cost_center'].queryset = ChartOfAccount.objects.filter(tenant=tenant)

class PayrollRunForm(forms.ModelForm):
    class Meta:
        model = PayrollRun
        fields = ['period_name', 'payment_date', 'status']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
