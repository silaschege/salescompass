from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from leads.models import Lead
from unittest.mock import patch

User = get_user_model()

class LeadSignalTests(TestCase):
    @patch('leads.signals.evaluate_assignment_rules.delay')
    def test_lead_creation_triggers_assignment(self, mock_task):
        """Test that creating a lead triggers the assignment task."""
        Lead.objects.create(
            first_name="Signal",
            last_name="Test",
            email="signal@example.com",
            company="Test Co",
            industry="tech"
        )
        
        self.assertTrue(mock_task.called)
        args, _ = mock_task.call_args
        self.assertEqual(args[0], 'leads')
        # args[1] is the lead ID, which we can't predict exactly but it should be an int
        self.assertIsInstance(args[1], int)

    @patch('leads.signals.evaluate_assignment_rules.delay')
    def test_lead_update_does_not_trigger_assignment(self, mock_task):
        """Test that updating a lead does not trigger assignment."""
        lead = Lead.objects.create(
            first_name="Update",
            last_name="Test",
            email="update@example.com",
            company="Test Co",
            industry="tech"
        )
        
        mock_task.reset_mock()
        
        lead.first_name = "Updated Name"
        lead.save()
        
        self.assertFalse(mock_task.called)
