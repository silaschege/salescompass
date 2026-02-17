from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from quality_control.models import InspectionRule, InspectionLog, NonConformanceReport, CAPA
from tenants.models import Tenant
import json

User = get_user_model()

class QCPhase3Tests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="QC Phase 3 Tenant", subdomain="qc3")
        self.user = User.objects.create_user(username="qc3_user", password="password", tenant=self.tenant)
        self.client = Client()
        self.client.login(username="qc3_user", password="password")
        
        self.rule = InspectionRule.objects.create(
            tenant=self.tenant,
            name="AQL Rule",
            sampling_type='acceptance_sampling',
            aql_level=1.0,
            inspection_level='II',
            check_list=[{"id": "test", "label": "Test", "type": "bool", "required": True}]
        )

    def test_sampling_api(self):
        # Test AQL calculation for Lot Size 100, Level II, AQL 1.0
        # According to sampling.py:
        # 100 is between 91-150 -> Level II code letter is 'F'
        # 'F' sample size is 20, Ac/Re for AQL 1.0 is (1, 2)
        response = self.client.get(reverse('quality_control:calculate_sample_api') + '?lot_size=100&aql=1.0&level=II')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['sample_size'], 20)
        self.assertEqual(data['acceptance_number'], 1)
        self.assertEqual(data['rejection_number'], 2)

    def test_capa_creation(self):
        # Create NCR first
        log = InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='fail', performed_by=self.user)
        ncr = NonConformanceReport.objects.get(inspection_log=log)
        
        # Create CAPA from NCR
        response = self.client.post(reverse('quality_control:capa_create'), {
            'title': "Systemic Process Improvement",
            'capa_type': "corrective",
            'description': "Addressing reoccurring issues",
            'source_ncr': ncr.pk,
            'root_cause': "Found in 5 whys",
            'action_plan': "Train staff, update machinery",
            'verification_plan': "Review next 10 batches",
            'status': "proposed"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CAPA.objects.count(), 1)
        capa = CAPA.objects.first()
        self.assertEqual(capa.source_ncr, ncr)

    def test_capa_status_workflow(self):
        capa = CAPA.objects.create(
            tenant=self.tenant,
            title="Initial CAPA",
            description="Testing status",
            action_plan="Plan",
            status="proposed"
        )
        response = self.client.post(reverse('quality_control:capa_update', args=[capa.pk]), {
            'title': "Initial CAPA",
            'description': "Testing status",
            'action_plan': "Plan",
            'status': "in_progress"
        })
        self.assertEqual(response.status_code, 302)
        capa.refresh_from_db()
        self.assertEqual(capa.status, "in_progress")
