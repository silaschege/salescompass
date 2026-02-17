from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from tenants.models import Tenant
from accounts.models import OrganizationMember, TeamRole, Territory
import datetime

class OrganizationMemberTests(TestCase):
    def setUp(self):
        # Create tenant and user
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.user = User.objects.create_user(
            username="testadmin", 
            email="admin@test.com", 
            password="password",
            tenant=self.tenant
        )
        self.member_user = User.objects.create_user(
            username="member", 
            email="member@test.com", 
            password="password",
            tenant=self.tenant
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Create Role and Territory
        self.role = TeamRole.objects.create(
            role_name="sales_rep", 
            label="Sales Rep", 
            tenant=self.tenant
        )
        self.territory = Territory.objects.create(
            territory_name="north", 
            label="North", 
            tenant=self.tenant
        )

    def test_create_organization_member(self):
        url = reverse('accounts:member_create')
        data = {
            'user': self.member_user.id,
            'role_ref': self.role.id,
            'territory_ref': self.territory.id,
            'quota_amount': 10000,
            'quota_period': 'monthly',
            'commission_rate': 10.0,
            'hire_date': '2023-01-01'
        }
        response = self.client.post(url, data)
        # Check if redirected (success)
        self.assertEqual(response.status_code, 302)
        
        # Verify creation
        self.assertTrue(OrganizationMember.objects.filter(user=self.member_user).exists())
        member = OrganizationMember.objects.get(user=self.member_user)
        self.assertEqual(member.role_ref, self.role)
        self.assertEqual(member.territory_ref, self.territory)

    def test_list_organization_members(self):
        # Create member first
        OrganizationMember.objects.create(
            user=self.member_user,
            role_ref=self.role,
            tenant=self.tenant
        )
        
        url = reverse('accounts:member_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "member@test.com")
