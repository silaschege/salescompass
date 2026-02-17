from django.test import TestCase
from django.urls import reverse
from core.models import User
from tenants.models import Tenant
from hr.models import Employee, PayrollRun, PayrollLine
from datetime import date
from decimal import Decimal

class PayslipAccessTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")
        self.user_emp = User.objects.create(
            email="emp@example.com",
            first_name="Emp",
            last_name="One",
            tenant=self.tenant
        )
        self.employee = Employee.objects.create(
            user=self.user_emp,
            tenant=self.tenant,
            employee_id="EMP001",
            hire_date=date.today(),
            position="Dev"
        )
        
        self.user_other = User.objects.create(
            email="other@example.com",
            first_name="Other",
            last_name="User",
            tenant=self.tenant
        )
        self.other_employee = Employee.objects.create(
            user=self.user_other,
            tenant=self.tenant,
            employee_id="EMP002",
            hire_date=date.today(),
            position="Dev"
        )

        self.payroll_run = PayrollRun.objects.create(
            tenant=self.tenant,
            period_name="Jan 2026",
            status='paid'
        )
        self.payslip = PayrollLine.objects.create(
            payroll_run=self.payroll_run,
            employee=self.employee,
            gross_salary=Decimal('5000.00'),
            net_salary=Decimal('4500.00'),
            tenant=self.tenant
        )

    def test_employee_can_access_own_payslip(self):
        self.client.force_login(self.user_emp)
        url = reverse('hr:payslip_detail', kwargs={'pk': self.payslip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_access_others_payslip(self):
        self.client.force_login(self.user_other)
        url = reverse('hr:payslip_detail', kwargs={'pk': self.payslip.pk})
        response = self.client.get(url)
        # Should return 404 because of view queryset filtering
        self.assertEqual(response.status_code, 404)

    def test_manager_can_access_any_payslip(self):
        # Create a manager/staff user
        manager_user = User.objects.create(
            email="manager@example.com",
            is_staff=True,
            tenant=self.tenant
        )
        self.client.force_login(manager_user)
        url = reverse('hr:payslip_detail', kwargs={'pk': self.payslip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
