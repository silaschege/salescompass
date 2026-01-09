from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenants.models import Tenant, TenantFeatureEntitlement
from billing.models import Plan, Subscription

User = get_user_model()

class TenantOnboardingFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('tenants:onboarding_signup')
        self.welcome_url = reverse('tenants:onboarding_welcome')
        self.tenant_info_url = reverse('tenants:onboarding_tenant_info')
        self.plan_selection_url = reverse('tenants:onboarding_plan_selection')
        self.subdomain_url = reverse('tenants:onboarding_subdomain')
        self.branding_url = reverse('tenants:onboarding_branding')
        self.complete_url = reverse('tenants:onboarding_complete')

        # Create a plan for testing
        self.plan = Plan.objects.create(
            name="Test Plan",
            price=10.00,
            is_active=True
        )

    def test_full_onboarding_flow(self):
        """
        Test the complete onboarding flow from signup to tenant creation.
        """
        # Step 1: Signup
        response = self.client.post(self.signup_url, {
            'email': 'newadmin@example.com',
            'first_name': 'New',
            'last_name': 'Admin',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.welcome_url)
        
        # Verify user created
        user = User.objects.get(email='newadmin@example.com')
        self.assertTrue(user.is_active)
        
        # Verify user is logged in
        self.assertIn('_auth_user_id', self.client.session)

        # Step 2: Welcome (GET)
        response = self.client.get(self.welcome_url)
        self.assertEqual(response.status_code, 200)

        # Step 3: Tenant Info
        response = self.client.post(self.tenant_info_url, {
            'company_name': 'My New Company',
            'company_description': 'A test company',
            'industry': 'technology',
            'company_size': '1-10',
            'primary_email': 'admin@company.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.plan_selection_url)
        
        # Verify session data
        self.assertEqual(self.client.session['onboarding_tenant_info']['company_name'], 'My New Company')

        # Step 4: Plan Selection
        # Note: The view expects JSON body for plan selection
        response = self.client.post(
            self.plan_selection_url, 
            {'selected_plan_id': self.plan.id}, 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

        # Step 5: Subdomain
        response = self.client.post(self.subdomain_url, {
            'subdomain': 'my-new-company'
        })
        self.assertEqual(response.status_code, 302)
        
        # Step 6: Data Residency (Default fallback)
        # Skipping explicitly since it defaults to session

        # Step 7: Branding
        response = self.client.post(self.branding_url, {
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
            'timezone': 'UTC',
            'date_format': '%Y-%m-%d',
            'currency': 'USD'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.complete_url)

        # Step 8: Completion (GET triggers creation)
        response = self.client.get(self.complete_url)
        self.assertEqual(response.status_code, 302) # Redirects to self on success
        
        # Verify Tenant Created
        tenant = Tenant.objects.get(name='My New Company')
        self.assertEqual(tenant.subdomain, 'my-new-company')
        self.assertEqual(tenant.primary_color, '#ff0000')
        self.assertEqual(tenant.tenant_admin, user)
        self.assertEqual(tenant.plan, self.plan)

        # Verify Subscription Created
        subscription = Subscription.objects.get(tenant=tenant)
        self.assertEqual(subscription.subscription_plan, self.plan)
        self.assertTrue(subscription.subscription_is_active)
        self.assertEqual(subscription.status, 'trialing')

        # Verify User Linked
        user.refresh_from_db()
        self.assertEqual(user.tenant, tenant)

