import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Lead, LeadStatus
from accounts.models import Account

User = get_user_model()

class LeadKanbanTests(TestCase):
    def setUp(self):
        # Create user and tenant
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            tenant_id='tenant1'
        )
        self.client.force_login(self.user)
        
        # Create Statuses
        self.status1 = LeadStatus.objects.create(
            name='new',
            label='New',
            order=1,
            tenant_id='tenant1'
        )
        self.status2 = LeadStatus.objects.create(
            name='qualified',
            label='Qualified',
            order=2,
            is_qualified=True,
            tenant_id='tenant1'
        )
        
        # Create Lead
        self.lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            company='Acme Corp',
            email='john@acme.com',
            status_ref=self.status1,
            status='new',
            lead_score=10,
            tenant_id='tenant1',
            owner=self.user
        )

    def test_kanban_view_status_code(self):
        """Test that the Lead Kanban view returns 200 OK."""
        url = reverse('leads:pipeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/pipeline_kanban.html')

    def test_kanban_view_context(self):
        """Test that the Kanban view context contains statuses and leads."""
        url = reverse('leads:pipeline')
        response = self.client.get(url)
        
        # Check statuses in context
        statuses = response.context['statuses']
        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0]['label'], 'New')
        
        # Check leads in status 1
        self.assertEqual(len(statuses[0]['leads']), 1)
        self.assertEqual(statuses[0]['leads'][0]['name'], 'John Doe')
        
        # Check status 2 is empty
        self.assertEqual(len(statuses[1]['leads']), 0)

    def test_update_status_ajax_success(self):
        """Test updating lead status via AJAX."""
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['new_status'], 'qualified')
        
        # Refresh lead from DB
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status_ref, self.status2)
        self.assertEqual(self.lead.status, 'qualified')
        
        # Check score updated (10 + 20 = 30)
        # Note: Logic adds 20 points for qualification
        self.assertEqual(self.lead.lead_score, 30)

    def test_update_status_invalid_status(self):
        """Test updating to a non-existent status."""
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': 99999
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['success'])

    def test_update_status_invalid_lead(self):
        """Test updating a non-existent lead."""
        url = reverse('leads:update_status', args=[99999])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_update_status_cross_tenant_isolation(self):
        """Test that a user cannot update a lead from another tenant."""
        # Create another user and tenant
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123',
            tenant_id='tenant2'
        )
        self.client.force_login(other_user)
        
        url = reverse('leads:update_status', args=[self.lead.id])
        data = {
            'status_id': self.status2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 404 because the lead is not found in tenant2
        self.assertEqual(response.status_code, 404)
