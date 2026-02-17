import os
import django
from django.test import TestCase
from core.models import User
from tenants.models import Tenant, TenantMember
from hr.models import Employee
from datetime import date

class HRTenantIntegrationTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", slug="test-tenant")
        self.user = User.objects.create(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            tenant=self.tenant
        )
        
    def test_employee_linkage_signal(self):
        """Test that creating an employee automatically links it to a TenantMember."""
        # Pre-condition: Create a TenantMember
        member = TenantMember.objects.create(
            user=self.user,
            tenant=self.tenant,
            status='active'
        )
        
        # Action: Create an Employee
        employee = Employee.objects.create(
            user=self.user,
            tenant=self.tenant,
            employee_id="EMP001",
            hire_date=date.today(),
            position="Software Engineer"
        )
        
        # Verification
        employee.refresh_from_db()
        self.assertEqual(employee.tenant_member, member)
        self.assertEqual(member.employee_profile, employee)
        
    def test_employee_sync_onboarding(self):
        """Test that creating an employee creates a TenantMember if missing."""
        # No TenantMember exists yet
        self.assertFalse(TenantMember.objects.filter(user=self.user).exists())
        
        # Action: Create an Employee
        employee = Employee.objects.create(
            user=self.user,
            tenant=self.tenant,
            employee_id="EMP002",
            hire_date=date.today(),
            position="Manager"
        )
        
        # Verification
        employee.refresh_from_db()
        self.assertIsNotNone(employee.tenant_member)
        self.assertEqual(employee.tenant_member.user, self.user)
        self.assertEqual(employee.tenant_member.status, 'active')
