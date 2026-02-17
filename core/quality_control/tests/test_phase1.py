from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from quality_control.models import InspectionRule, InspectionLog, NonConformanceReport, InspectionAttachment
from tenants.models import Tenant

User = get_user_model()

class QCPhase1Tests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.user = User.objects.create_user(username="testuser", password="password", tenant=self.tenant)
        self.client = Client()
        self.client.force_login(self.user)
        
        self.rule = InspectionRule.objects.create(
            tenant=self.tenant,
            name="Receive Check",
            check_list=[
                {"id": "item_1", "label": "Visual", "type": "bool", "required": True},
                {"id": "item_2", "label": "Width", "type": "number", "required": False}
            ]
        )

    def test_checklist_storage(self):
        """Test that checklist JSON is stored correctly."""
        self.assertEqual(len(self.rule.check_list), 2)
        self.assertEqual(self.rule.check_list[0]['label'], 'Visual')

    def test_inspection_log_creation(self):
        """Test creating an inspection log with results."""
        results = {"item_1": "pass", "item_2": "15"}
        log = InspectionLog.objects.create(
            tenant=self.tenant,
            rule=self.rule,
            inspector=self.user,
            source_reference="PO-123",
            status="passed",
            results_data=results
        )
        self.assertEqual(log.results_data, results)

    def test_ncr_automation(self):
        """Test that NCR is created on failed inspection."""
        results = {"item_1": "fail"}
        log = InspectionLog.objects.create(
            tenant=self.tenant,
            rule=self.rule,
            inspector=self.user,
            source_reference="PO-FAILED",
            status="failed", # Should trigger signal
            results_data=results
        )
        
        self.assertTrue(NonConformanceReport.objects.filter(inspection_log=log).exists())
    
    def test_ncr_no_duplication(self):
        """Test that NCR is not duplicated if already exists."""
        results = {"item_1": "fail"}
        log = InspectionLog.objects.create(
            tenant=self.tenant,
            rule=self.rule,
            inspector=self.user,
            source_reference="PO-FAILED",
            status="failed",
            results_data=results
        )
        # First one created
        first_count = NonConformanceReport.objects.filter(inspection_log=log).count()
        self.assertEqual(first_count, 1)

        # Trigger save again
        log.save()
        
        second_count = NonConformanceReport.objects.filter(inspection_log=log).count()
        self.assertEqual(second_count, 1)

    def test_rule_detail_api(self):
        """Test the rule detail API endpoint."""
        url = reverse('quality_control:rule_detail_api', args=[self.rule.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.rule.pk)
        self.assertEqual(len(data['check_list']), 2)
