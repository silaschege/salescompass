import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Opportunity, OpportunityStage
from accounts.models import Account
from core.models import TenantModel

User = get_user_model()

class OpportunityKanbanTests(TestCase):
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
        
        # Create Account
        self.account = Account.objects.create(
            name='Test Account',
            tenant_id='tenant1',
            owner=self.user
        )
        
        # Create Stages
        self.stage1 = OpportunityStage.objects.create(
            name='Prospecting',
            order=1,
            probability=10,
            tenant_id='tenant1'
        )
        self.stage2 = OpportunityStage.objects.create(
            name='Qualification',
            order=2,
            probability=30,
            tenant_id='tenant1'
        )
        
        # Create Opportunity
        self.opportunity = Opportunity.objects.create(
            name='Test Opportunity',
            account=self.account,
            amount=10000,
            stage=self.stage1,
            close_date='2025-12-31',
            probability=0.1,
            tenant_id='tenant1',
            owner=self.user
        )

    def test_kanban_view_status_code(self):
        """Test that the Kanban view returns 200 OK."""
        url = reverse('opportunities:pipeline')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'opportunities/pipeline_kanban.html')

    def test_kanban_view_context(self):
        """Test that the Kanban view context contains stages and opportunities."""
        url = reverse('opportunities:pipeline')
        response = self.client.get(url)
        
        # Check stages in context
        stages = response.context['stages']
        self.assertEqual(len(stages), 2)
        self.assertEqual(stages[0]['name'], 'Prospecting')
        
        # Check opportunities in stage 1
        self.assertEqual(len(stages[0]['opportunities']), 1)
        self.assertEqual(stages[0]['opportunities'][0]['name'], 'Test Opportunity')
        
        # Check stage 2 is empty
        self.assertEqual(len(stages[1]['opportunities']), 0)

    def test_update_stage_ajax_success(self):
        """Test updating opportunity stage via AJAX."""
        url = reverse('opportunities:update_stage', args=[self.opportunity.id])
        data = {
            'stage_id': self.stage2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['new_stage'], 'Qualification')
        
        # Refresh opportunity from DB
        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.stage, self.stage2)
        # Check probability updated (30% -> 0.3)
        self.assertEqual(self.opportunity.probability, 0.3)

    def test_update_stage_invalid_stage(self):
        """Test updating to a non-existent stage."""
        url = reverse('opportunities:update_stage', args=[self.opportunity.id])
        data = {
            'stage_id': 99999
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['success'])

    def test_update_stage_invalid_opportunity(self):
        """Test updating a non-existent opportunity."""
        url = reverse('opportunities:update_stage', args=[99999])
        data = {
            'stage_id': self.stage2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_update_stage_cross_tenant_isolation(self):
        """Test that a user cannot update an opportunity from another tenant."""
        # Create another user and tenant
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123',
            tenant_id='tenant2'
        )
        self.client.force_login(other_user)
        
        url = reverse('opportunities:update_stage', args=[self.opportunity.id])
        data = {
            'stage_id': self.stage2.id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 404 because the opportunity is not found in tenant2
        self.assertEqual(response.status_code, 404)
