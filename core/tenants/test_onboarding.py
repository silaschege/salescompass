from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from .models import Tenant, TenantSettings, DataResidencySettings, TenantFeatureEntitlement, WhiteLabelSettings
from billing.models import Plan, Subscription
import json

class OnboardingIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.login(username='testuser', password='password123')
        self.plan = Plan.objects.create(name='Pro Plan', price=29.99, is_active=True)

    def test_full_onboarding_flow(self):
        # Step 1: Welcome
        response = self.client.get(reverse('tenants:onboarding_welcome'))
        self.assertEqual(response.status_code, 200)

        # Step 2: Tenant Info
        response = self.client.post(reverse('tenants:onboarding_tenant_info'), {
            'company_name': 'Acme Corp',
            'company_description': 'A great company',
            'industry': 'technology',
            'company_size': '11-50',
            'primary_email': 'contact@acme.com'
        })
        self.assertRedirects(response, reverse('tenants:onboarding_plan_selection'))

        # Step 3: Plan Selection
        response = self.client.post(
            reverse('tenants:onboarding_plan_selection'),
            json.dumps({'selected_plan_id': self.plan.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Step 4: Subdomain Assignment
        response = self.client.post(reverse('tenants:onboarding_subdomain'), {
            'subdomain': 'acme-corp'
        })
        self.assertRedirects(response, reverse('tenants:onboarding_data_residency'))

        # Step 5: Data Residency (Replaces DB Init)
        response = self.client.post(reverse('tenants:onboarding_data_residency'), {
            'primary_region': 'US'
        })
        self.assertRedirects(response, reverse('tenants:onboarding_branding'))

        # Step 6: Branding
        response = self.client.post(reverse('tenants:onboarding_branding'), {
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'timezone': 'UTC'
        })
        self.assertRedirects(response, reverse('tenants:onboarding_admin_setup'))

        # Step 7: Admin Setup
        response = self.client.post(reverse('tenants:onboarding_admin_setup'))
        self.assertRedirects(response, reverse('tenants:onboarding_complete'))

        # Step 8: Complete (Triggers Creation)
        response = self.client.get(reverse('tenants:onboarding_complete'))
        self.assertEqual(response.status_code, 200)

        # Verify Tenant Creation
        tenant = Tenant.objects.get(name='Acme Corp')
        self.assertEqual(tenant.subdomain, 'acme-corp')
        self.assertEqual(tenant.plan, self.plan)
        
        # Verify Related Models
        self.assertTrue(Subscription.objects.filter(tenant=tenant).exists())
        self.assertTrue(DataResidencySettings.objects.filter(tenant=tenant, primary_region='US').exists())
        self.assertTrue(WhiteLabelSettings.objects.filter(tenant=tenant).exists())
        self.assertTrue(TenantFeatureEntitlement.objects.filter(tenant=tenant).exists())
        self.assertTrue(TenantSettings.objects.filter(tenant=tenant).exists())
        
        # Verify User Assignment
        self.user.refresh_from_db()
        self.assertEqual(self.user.tenant, tenant)
