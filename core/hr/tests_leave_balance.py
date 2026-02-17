from django.test import TestCase
from core.models import User
from tenants.models import Tenant
from hr.models import Employee, LeaveRequest, LeaveBalance
from hr.services import LeaveService
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

class LeaveBalanceTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")
        self.user = User.objects.create(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            tenant=self.tenant
        )
        self.employee = Employee.objects.create(
            user=self.user,
            tenant=self.tenant,
            employee_id="EMP001",
            hire_date=date.today(),
            position="Engineer"
        )
        self.balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type='annual',
            entitled_days=20,
            used_days=0,
            year=timezone.now().year,
            tenant=self.tenant
        )

    def test_leave_request_validation(self):
        # Test valid request
        can_approve, error = LeaveService.check_balance(self.employee, 'annual', 5)
        self.assertTrue(can_approve)
        
        # Test invalid request (more than balance)
        can_approve, error = LeaveService.check_balance(self.employee, 'annual', 25)
        self.assertFalse(can_approve)
        self.assertIn("Insufficient balance", error)

    def test_balance_deduction(self):
        request = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4), # 5 days
            status='approved',
            tenant=self.tenant
        )
        
        LeaveService.deduct_balance(request)
        self.balance.refresh_from_db()
        
        self.assertEqual(self.balance.used_days, Decimal('5.00'))
        self.assertEqual(self.balance.remaining_days, Decimal('15.00'))
