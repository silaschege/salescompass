from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from core.views import SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView, SalesCompassUpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Employee, LeaveRequest, Department, Attendance, PayrollRun
from .forms import EmployeeForm, LeaveRequestForm, DepartmentForm, PayrollRunForm
from .services import EmployeeService

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
        
        # My Leave Balances
        from django.utils import timezone
        try:
            employee = self.request.user.employee_profile
            context['my_balances'] = LeaveBalance.objects.filter(employee=employee, year=timezone.now().year)
        except Employee.DoesNotExist:
            context['my_balances'] = None
        
        # My Recent Payslips
        try:
            employee = self.request.user.employee_profile
            context['my_payslips'] = PayrollLine.objects.filter(employee=employee).select_related('payroll_run').order_by('-payroll_run__payment_date')[:3]
        except Employee.DoesNotExist:
            context['my_payslips'] = None
            
        # Payroll Insights (IAS 19 focus)
        latest_payroll = PayrollRun.objects.filter(tenant=tenant, status='paid').order_by('-payment_date').first()
        if latest_payroll:
            context['latest_payroll_amount'] = latest_payroll.total_gross
            context['latest_payroll_period'] = latest_payroll.period_name
            
        context['recent_runs'] = PayrollRun.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        
        # Performance Goals
        context['active_goals_count'] = PerformanceGoal.objects.filter(tenant=tenant, status='active').count()
        try:
            employee = self.request.user.employee_profile
            context['my_goals'] = PerformanceGoal.objects.filter(employee=employee, status__in=['active', 'completed']).order_by('-target_date')[:3]
        except Employee.DoesNotExist:
            context['my_goals'] = None
            
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
    
    def form_valid(self, form):
        response = super().form_valid(form)
        EmployeeService.sync_tenant_member(self.object)
        return response

class EmployeeUpdateView(SalesCompassUpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employee_list')
    success_message = "Employee updated successfully."
    
    def form_valid(self, form):
        response = super().form_valid(form)
        EmployeeService.ensure_consistency(self.object)
        return response

class EmployeeDetailView(SalesCompassDetailView):
    model = Employee
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.tenant_member:
            context['membership'] = self.object.tenant_member
        return context

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
            
            # Balance check
            from .services import LeaveService
            days = LeaveService.get_requested_days(form.cleaned_data['start_date'], form.cleaned_data['end_date'])
            is_valid, error_msg = LeaveService.check_balance(employee, form.cleaned_data['leave_type'], days)
            
            if not is_valid:
                messages.error(self.request, error_msg)
                return self.form_invalid(form)
                
            return super().form_valid(form)
        except Employee.DoesNotExist:
            messages.error(self.request, "You do not have an employee profile linked to your user account.")
            return redirect('hr:dashboard')

from .models import LeaveBalance

class LeaveBalanceListView(SalesCompassListView):
    model = LeaveBalance
    template_name = 'hr/leave_balance_list.html'
    context_object_name = 'balances'
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Non-managers see only their own balance
        if not self.request.user.is_staff: # Simplification: check if user is staff/manager
             try:
                 employee = self.request.user.employee_profile
                 qs = qs.filter(employee=employee)
             except Employee.DoesNotExist:
                 qs = qs.none()
        return qs

class LeaveApprovalView(View):
    """
    Action view for managers to approve leave requests and deduct balance.
    """
    def post(self, request, pk):
        leave_request = get_object_or_404(LeaveRequest, pk=pk, tenant=request.user.tenant)
        if leave_request.status == 'pending':
            leave_request.status = 'approved'
            leave_request.approved_by = request.user
            leave_request.save()
            
            # Deduct balance
            from .services import LeaveService
            LeaveService.deduct_balance(leave_request)
            
            messages.success(request, f"Leave request for {leave_request.employee} approved and balance updated.")
        else:
            messages.warning(request, f"Leave request is already {leave_request.status}.")
            
        return redirect('hr:leave_list')

# --- Attendance ---

class AttendanceListView(SalesCompassListView):
    model = Attendance
    template_name = 'hr/attendance_list.html'
    context_object_name = 'records'

class AttendanceActionView(TemplateView):
    template_name = 'hr/attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        try:
            employee = self.request.user.employee_profile
            today = timezone.now().date()
            context['attendance'] = Attendance.objects.filter(employee=employee, date=today).first()
        except Employee.DoesNotExist:
            context['attendance'] = None
        return context

    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        try:
            employee = request.user.employee_profile
            action = request.POST.get('action') # 'in' or 'out'
            
            if action == 'in':
                Attendance.objects.get_or_create(
                    employee=employee,
                    date=timezone.now().date(),
                    tenant=request.user.tenant,
                    defaults={'clock_in': timezone.now().time(), 'status': 'present'}
                )
                messages.success(request, "Clocked in successfully.")
            elif action == 'out':
                today = timezone.now().date()
                attendance = Attendance.objects.filter(employee=employee, date=today).first()
                if attendance:
                    attendance.clock_out = timezone.now().time()
                    attendance.save()
                    messages.success(request, "Clocked out successfully.")
                else:
                    messages.error(request, "No clock-in record found for today.")
        except Employee.DoesNotExist:
            messages.error(request, "Employee profile not found.")
            
        return redirect('hr:attendance')

# --- Payroll ---

class PayrollDashboardView(SalesCompassListView):
    model = PayrollRun
    template_name = 'hr/payroll_dashboard.html'
    context_object_name = 'payroll_runs'

class PayrollCreateView(SalesCompassCreateView):
    model = PayrollRun
    form_class = PayrollRunForm
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

from .models import PayrollLine

class PayslipDetailView(SalesCompassDetailView):
    model = PayrollLine
    template_name = 'hr/payslip_detail.html'
    context_object_name = 'line'

    def get_queryset(self):
        qs = super().get_queryset()
        # Security: Employee can only see their own payslip
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.employee_profile
                qs = qs.filter(employee=employee)
            except Employee.DoesNotExist:
                qs = qs.none()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['run'] = self.object.payroll_run
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
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')

class DepartmentUpdateView(SalesCompassUpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Employee, Attendance

class BiometricAttendanceAPIView(APIView):
    """
    API endpoint for biometric devices to push attendance logs.
    Expects: { "employee_id": "...", "timestamp": "...", "action": "in/out" }
    """
    def post(self, request):
        data = request.data
        employee_id = data.get('employee_id')
        timestamp_str = data.get('timestamp')
        action = data.get('action') # 'in' or 'out'

        if not all([employee_id, timestamp_str, action]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(employee_id=employee_id, tenant=request.user.tenant)
            dt = timezone.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            date = dt.date()
            time = dt.time()

            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=date,
                tenant=request.user.tenant,
                defaults={'status': 'present'}
            )

            if action == 'in':
                attendance.clock_in = time
            elif action == 'out':
                attendance.clock_out = time
            
            attendance.biometric_ref = data.get('biometric_ref', 'api-ingest')
            attendance.save()

            return Response({"status": "success", "id": attendance.id}, status=status.HTTP_201_CREATED)

        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Performance Management ---

from .models import PerformanceGoal, GoalReview

class PerformanceGoalListView(SalesCompassListView):
    model = PerformanceGoal
    template_name = 'hr/goal_list.html'
    context_object_name = 'goals'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            try:
                employee = self.request.user.employee_profile
                qs = qs.filter(employee=employee)
            except Employee.DoesNotExist:
                qs = qs.none()
        return qs

class PerformanceGoalCreateView(SalesCompassCreateView):
    model = PerformanceGoal
    fields = ['employee', 'title', 'description', 'weight', 'target_date', 'status']
    template_name = 'hr/goal_form.html'
    success_url = reverse_lazy('hr:goal_list')
    success_message = "Performance goal set successfully."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['target_date'].widget = forms.DateInput(attrs={'type': 'date'})
        # If not staff, auto-set employee and hide field
        if not self.request.user.is_staff:
            try:
                form.fields['employee'].initial = self.request.user.employee_profile
                form.fields['employee'].widget = forms.HiddenInput()
            except Employee.DoesNotExist:
                pass
        return form

class PerformanceGoalUpdateView(SalesCompassUpdateView):
    model = PerformanceGoal
    fields = ['title', 'description', 'weight', 'target_date', 'status', 'progress_percentage']
    template_name = 'hr/goal_form.html'
    success_url = reverse_lazy('hr:goal_list')
    success_message = "Performance goal updated."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['target_date'].widget = forms.DateInput(attrs={'type': 'date'})
        return form

class GoalReviewCreateView(SalesCompassCreateView):
    model = GoalReview
    fields = ['score', 'comments']
    template_name = 'hr/goal_review_form.html'
    success_url = reverse_lazy('hr:goal_list')
    success_message = "Goal review submitted."

    def form_valid(self, form):
        form.instance.goal_id = self.kwargs['goal_pk']
        form.instance.reviewer = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['goal'] = get_object_or_404(PerformanceGoal, pk=self.kwargs['goal_pk'], tenant=self.request.user.tenant)
        return context
