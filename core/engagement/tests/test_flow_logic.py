from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from tenants.models import Tenant
from engagement.models import EngagementEvent
from accounts.models import Account, Contact
from leads.models import Lead
from engagement.views import EngagementEventDetailView

User = get_user_model()

class FlowLogicTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", subdomain="test")
        self.user = User.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="password",
            tenant=self.tenant
        )
        self.factory = RequestFactory()

        # Create entities - Note: Account in EngagementEvent links to Account (Company) or User (Legacy)
        # We'll use the proper Account (Company) model from accounts app
        self.account = Account.objects.create(name="Test Account", tenant=self.tenant)
        self.contact = Contact.objects.create(first_name="John", last_name="Doe", email="john@example.com", account=self.account, tenant=self.tenant)
        self.lead = Lead.objects.create(first_name="Jane", last_name="Smith", email="jane@example.com", tenant=self.tenant)

    def test_primary_entity_identification(self):
        """Test that EngagementEvent correctly identifies its primary entity."""
        # Contact event
        event_contact = EngagementEvent.objects.create(
            tenant_id=self.tenant.id,
            event_type='email_sent',
            title="Email to Contact",
            contact=self.contact,
            created_by=self.user
        )
        self.assertEqual(event_contact.primary_entity, self.contact)
        self.assertEqual(event_contact.primary_entity_name, f"{self.contact.first_name} {self.contact.last_name}")

        # Lead event
        event_lead = EngagementEvent.objects.create(
            tenant_id=self.tenant.id,
            event_type='lead_source',
            title="Lead Source",
            lead=self.lead,
            created_by=self.user
        )
        self.assertEqual(event_lead.primary_entity, self.lead)
        self.assertEqual(event_lead.primary_entity_name, f"{self.lead.first_name} {self.lead.last_name}")

        # Account event
        event_account = EngagementEvent.objects.create(
            tenant_id=self.tenant.id,
            event_type='subscription_created',
            title="Account Sub",
            account_company=self.account,
            created_by=self.user
        )
        self.assertEqual(event_account.primary_entity, self.account)
        self.assertEqual(event_account.primary_entity_name, self.account.name)

    def test_engagement_flow_aggregation(self):
        """Test that the detail view correctly aggregates all related events."""
        # Create multiple events for the same contact
        EngagementEvent.objects.create(
            tenant_id=self.tenant.id,
            event_type='email_sent',
            title="Email 1",
            contact=self.contact,
            created_by=self.user,
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        event2 = EngagementEvent.objects.create(
            tenant_id=self.tenant.id,
            event_type='call_logged',
            title="Call 1",
            contact=self.contact,
            created_by=self.user,
            created_at=timezone.now()
        )

        view = EngagementEventDetailView()
        request = self.factory.get(f'/engagement/events/{event2.pk}/')
        request.user = self.user
        view.request = request
        view.object = event2
        view.kwargs = {'pk': event2.pk}

        context = view.get_context_data()
        
        self.assertIn('interaction_flow', context)
        self.assertEqual(len(context['interaction_flow']), 2)
        # Check chronological order (newest first)
        self.assertEqual(context['interaction_flow'][0].title, "Call 1")
        self.assertEqual(context['interaction_flow'][1].title, "Email 1")
        
        # Verify interaction shortcuts data
        self.assertEqual(context['target_email'], self.contact.email)
        self.assertIn(context['entity_type'], ['contact', 'lead', 'account'])
