from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Employee, LeaveRequest, Department, Attendance, PayrollRun
from .forms import EmployeeForm, LeaveRequestForm

class HRDashboardView(TemplateView):
    template_name = 'hr/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        
        # Workforce KPIs
        active_employees = Employee.objects.filter(tenant=tenant, is_active=True)
        context['employee_count'] = active_employees.count()
        context['fte_count'] = active_employees.filter(employment_type='full_time').count()
        
        # Leave Analytics
        context['pending_leaves'] = LeaveRequest.objects.filter(tenant=tenant, status='pending').count()
        
        # Payroll Insights (IAS 19 focus)
        latest_payroll = PayrollRun.objects.filter(tenant=tenant, status='paid').order_by('-payment_date').first()
        if latest_payroll:
            context['latest_payroll_amount'] = latest_payroll.total_gross
            context['latest_payroll_period'] = latest_payroll.period_name
            
        context['recent_runs'] = PayrollRun.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        
        return context

# --- Employee Management ---

class EmployeeListView(SalesCompassListView):
    model = Employee
    template_name = 'hr/employee_list.html'
    context_object_name = 'employees'

class EmployeeCreateView(SalesCompassCreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    success_message = "Employee added successfully."

class EmployeeUpdateView(SalesCompassUpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    success_message = "Employee updated successfully."

class EmployeeDetailView(SalesCompassDetailView):
    model = Employee
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'

# --- Leave Management ---

class LeaveRequestListView(SalesCompassListView):
    model = LeaveRequest
    template_name = 'hr/leave_list.html'
    context_object_name = 'leaves'

class LeaveRequestCreateView(SalesCompassCreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave_form.html'
    success_url = reverse_lazy('hr:leave_list')
    
    def form_valid(self, form):
        # Auto-link to the employee record of the logged-in user
        try:
            employee = self.request.user.employee_profile
            form.instance.employee = employee
            return super().form_valid(form)
        except Employee.DoesNotExist:
            messages.error(self.request, "You do not have an employee profile linked to your user account.")
            return redirect('hr:dashboard')

# --- Attendance ---

class AttendanceListView(SalesCompassListView):
    model = Attendance
    template_name = 'hr/attendance_list.html'
    context_object_name = 'attendance_records'

# --- Payroll ---

class PayrollDashboardView(SalesCompassListView):
    model = PayrollRun
    template_name = 'hr/payroll_dashboard.html'
    context_object_name = 'payroll_runs'

class PayrollCreateView(SalesCompassCreateView):
    model = PayrollRun
    fields = ['period_name', 'payment_date', 'status']
    template_name = 'hr/payroll_form.html'
    success_url = reverse_lazy('hr:payroll_dashboard')
    success_message = "Payroll run created."

class PayrollDetailView(SalesCompassDetailView):
    model = PayrollRun
    template_name = 'hr/payroll_detail.html'
    context_object_name = 'run'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lines'] = self.object.lines.all().select_related('employee', 'employee__user')
        return context

class PayrollAccrualActionView(View):
    """
    Triggers GL accrual for a payroll run.
    """
    def post(self, request, pk):
        run = get_object_or_404(PayrollRun, pk=pk, tenant=request.user.tenant)
        if not run.is_accrued:
            try:
                from .services import PayrollIntegrationService
                PayrollIntegrationService.post_accrual(run, request.user)
                messages.success(request, "Payroll accrued to General Ledger successfully.")
            except Exception as e:
                messages.error(request, f"Accrual failed: {str(e)}")
        return redirect('hr:payroll_detail', pk=pk)

class PayrollSettleActionView(View):
    """
    Triggers payment settlement for a payroll run.
    """
    def post(self, request, pk):
        run = get_object_or_404(PayrollRun, pk=pk, tenant=request.user.tenant)
        if run.is_accrued and run.status != 'paid':
            try:
                from .services import PayrollIntegrationService
                PayrollIntegrationService.post_settlement(run, request.user)
                messages.success(request, "Payroll settlement and payment recorded.")
            except Exception as e:
                messages.error(request, f"Settlement failed: {str(e)}")
        return redirect('hr:payroll_detail', pk=pk)

# --- Departments ---

class DepartmentListView(SalesCompassListView):
    model = Department
    template_name = 'hr/department_list.html'
    context_object_name = 'departments'

class DepartmentCreateView(SalesCompassCreateView):
    model = Department
    fields = ['name', 'manager', 'cost_center']
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')

class DepartmentUpdateView(SalesCompassUpdateView):
    model = Department
    fields = ['name', 'manager', 'cost_center']
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
