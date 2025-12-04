from django.test import TestCase
from django.contrib.auth import get_user_model
from settings_app.models import AssignmentRule, Territory, TeamMember
from leads.models import Lead
from automation.assignment_engine import evaluate_assignment_rules

User = get_user_model()

class AssignmentRuleTests(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        
        # Create team members
        self.tm1 = TeamMember.objects.create(user=self.user1, status='active')
        self.tm2 = TeamMember.objects.create(user=self.user2, status='active')
        
        # Create territory
        self.territory = Territory.objects.create(name='north_america', country_codes=['US', 'CA'])
        self.tm1.territory = self.territory
        self.tm1.save()

    def test_round_robin_assignment(self):
        rule = AssignmentRule.objects.create(
            name="Round Robin Rule",
            module="leads",
            rule_type="round_robin",
            priority=10
        )
        rule.assignees.add(self.user1, self.user2)
        
        lead1 = Lead.objects.create(first_name="Lead", last_name="1", email="l1@example.com")
        lead2 = Lead.objects.create(first_name="Lead", last_name="2", email="l2@example.com")
        
        # First assignment
        evaluate_assignment_rules('leads', lead1.id)
        lead1.refresh_from_db()
        self.assertIsNotNone(lead1.owner)
        first_owner = lead1.owner
        
        # Second assignment
        evaluate_assignment_rules('leads', lead2.id)
        lead2.refresh_from_db()
        self.assertIsNotNone(lead2.owner)
        self.assertNotEqual(lead2.owner, first_owner)

    def test_territory_assignment(self):
        rule = AssignmentRule.objects.create(
            name="Territory Rule",
            module="leads",
            rule_type="territory",
            priority=10
        )
        rule.assignees.add(self.user1, self.user2)
        
        # Lead in US should go to user1 (who is in North America territory)
        lead = Lead.objects.create(first_name="US", last_name="Lead", email="us@example.com", country="US")
        
        evaluate_assignment_rules('leads', lead.id)
        lead.refresh_from_db()
        self.assertEqual(lead.owner, self.user1)

    def test_criteria_assignment(self):
        rule = AssignmentRule.objects.create(
            name="Tech Industry Rule",
            module="leads",
            rule_type="criteria",
            criteria={"industry": "Tech"},
            priority=10
        )
        rule.assignees.add(self.user2)
        
        lead = Lead.objects.create(first_name="Tech", last_name="Lead", email="tech@example.com", industry="Tech")
        
        evaluate_assignment_rules('leads', lead.id)
        lead.refresh_from_db()
        self.assertEqual(lead.owner, self.user2)
        
    def test_no_match(self):
        rule = AssignmentRule.objects.create(
            name="Specific Rule",
            module="leads",
            rule_type="criteria",
            criteria={"industry": "Finance"},
            priority=10
        )
        rule.assignees.add(self.user1)
        
        lead = Lead.objects.create(first_name="Other", last_name="Lead", email="other@example.com", industry="Tech")
        
        evaluate_assignment_rules('leads', lead.id)
        lead.refresh_from_db()
        self.assertIsNone(lead.owner)
