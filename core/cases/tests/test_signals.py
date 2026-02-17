from django.test import TestCase
from django.contrib.auth import get_user_model
from cases.models import Case
from accounts.models import Account
from unittest.mock import patch

User = get_user_model()

class CaseSignalTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="Test Account", industry="tech")

    @patch('cases.signals.evaluate_assignment_rules.delay')
    def test_case_creation_triggers_assignment(self, mock_task):
        """Test that creating a case triggers the assignment task."""
        Case.objects.create(
            subject="Signal Test Case",
            description="Test Description",
            account=self.account,
            priority="medium"
        )
        
        self.assertTrue(mock_task.called)
        args, _ = mock_task.call_args
        self.assertEqual(args[0], 'cases')
        self.assertIsInstance(args[1], int)

    @patch('cases.signals.evaluate_assignment_rules.delay')
    def test_case_update_does_not_trigger_assignment(self, mock_task):
        """Test that updating a case does not trigger assignment."""
        case = Case.objects.create(
            subject="Update Test Case",
            description="Test Description",
            account=self.account,
            priority="medium"
        )
        
        mock_task.reset_mock()
        
        case.subject = "Updated Subject"
        case.save()
        
        self.assertFalse(mock_task.called)
