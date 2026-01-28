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

    # Attendance
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),

    # Payroll
    path('payroll/', views.PayrollDashboardView.as_view(), name='payroll_dashboard'),
    path('payroll/run/', views.PayrollCreateView.as_view(), name='payroll_create'),
    path('payroll/<int:pk>/', views.PayrollDetailView.as_view(), name='payroll_detail'),
    path('payroll/<int:pk>/accrual/', views.PayrollAccrualActionView.as_view(), name='payroll_accrual'),
    path('payroll/<int:pk>/settle/', views.PayrollSettleActionView.as_view(), name='payroll_settle'),

    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
]
