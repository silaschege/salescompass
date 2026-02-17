from django.test import TestCase
from django.urls import reverse
from core.models import User
from tenants.models import Tenant
from hr.models import Employee, LeavePolicy, LeaveBalance, Attendance, PerformanceGoal
from hr.services import LeaveAccrualService
from decimal import Decimal
from datetime import date, datetime
from rest_framework.test import APIClient

class HRPhase2Test(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Phase 2 Tenant", slug="phase2")
        self.user = User.objects.create(
            email="manager@example.com",
            tenant=self.tenant,
            is_staff=True
        )
        self.employee = Employee.objects.create(
            user=self.user,
            tenant=self.tenant,
            employee_id="PH2-001",
            salary=Decimal('2600.00'), # $10/day simplified
            hire_date=date.today(),
            position="Manager"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_leave_accrual_logic(self):
        policy = LeavePolicy.objects.create(
            tenant=self.tenant,
            name="Annual Leave",
            leave_type='annual',
            annual_entitlement=Decimal('24.00'),
            accrual_frequency='monthly'
        )
        
        # Run accrual
        results = LeaveAccrualService.run_accruals(self.tenant, self.user)
        
        # Check balance
        balance = LeaveBalance.objects.get(employee=self.employee, leave_type='annual')
        # 24 / 12 = 2.0 days
        self.assertEqual(balance.entitled_days, Decimal('2.00'))
        
        # Check accounting entry exists (simplistic check)
        from accounting.models import JournalEntry
        journals = JournalEntry.objects.filter(tenant=self.tenant, reference="LV-ACCRUAL")
        self.assertTrue(journals.exists())

    def test_biometric_api(self):
        url = reverse('hr:api_biometric_attendance')
        data = {
            "employee_id": "PH2-001",
            "timestamp": "2026-01-30T08:00:00Z",
            "action": "in",
            "biometric_ref": "DEVICE-01"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        
        attendance = Attendance.objects.get(employee=self.employee, date="2026-01-30")
        self.assertEqual(attendance.clock_in.hour, 8)
        self.assertEqual(attendance.biometric_ref, "DEVICE-01")

    def test_performance_goal_access(self):
        goal = PerformanceGoal.objects.create(
            tenant=self.tenant,
            employee=self.employee,
            title="Increase Sales",
            target_date=date.today(),
            status='active'
        )
        
        # Test List View
        url = reverse('hr:goal_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Increase Sales")
