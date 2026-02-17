from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Dashboard
    path('', views.HRDashboardView.as_view(), name='dashboard'),
    
    # Employees
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_update'),

    # Leave Management
    path('leave/', views.LeaveRequestListView.as_view(), name='leave_list'),
    path('leave/request/', views.LeaveRequestCreateView.as_view(), name='leave_create'),
    path('leave/<int:pk>/approve/', views.LeaveApprovalView.as_view(), name='leave_approve'),
    path('leave/balances/', views.LeaveBalanceListView.as_view(), name='leave_balance_list'),

    # Attendance
    path('attendance/', views.AttendanceActionView.as_view(), name='attendance'),
    path('attendance/history/', views.AttendanceListView.as_view(), name='attendance_history'),

    # Payroll
    path('payroll/', views.PayrollDashboardView.as_view(), name='payroll_dashboard'),
    path('payroll/run/', views.PayrollCreateView.as_view(), name='payroll_create'),
    path('payroll/<int:pk>/', views.PayrollDetailView.as_view(), name='payroll_detail'),
    path('payroll/payslip/<int:pk>/', views.PayslipDetailView.as_view(), name='payslip_detail'),
    path('payroll/<int:pk>/accrual/', views.PayrollAccrualActionView.as_view(), name='payroll_accrual'),
    path('payroll/<int:pk>/settle/', views.PayrollSettleActionView.as_view(), name='payroll_settle'),

    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),

    # Performance Goals
    path('goals/', views.PerformanceGoalListView.as_view(), name='goal_list'),
    path('goals/add/', views.PerformanceGoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:pk>/edit/', views.PerformanceGoalUpdateView.as_view(), name='goal_edit'),
    path('goals/<int:goal_pk>/review/', views.GoalReviewCreateView.as_view(), name='goal_review'),

    # API
    path('api/attendance/biometric/', views.BiometricAttendanceAPIView.as_view(), name='api_biometric_attendance'),
]
