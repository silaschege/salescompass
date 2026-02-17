from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from quality_control.models import InspectionRule, InspectionLog, NonConformanceReport
from tenants.models import Tenant
import json

User = get_user_model()

class QCPhase2Tests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="QC Tenant", subdomain="qc")
        self.user = User.objects.create_user(username="qc_user", password="password", tenant=self.tenant)
        self.client = Client()
        self.client.login(username="qc_user", password="password")
        
        self.rule = InspectionRule.objects.create(
            tenant=self.tenant,
            name="Measurement Rule",
            check_list=[{"id": "weight", "label": "Weight", "type": "number", "required": True}]
        )

    def test_dashboard_metrics(self):
        # Create 2 passed and 1 failed log
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='pass', performed_by=self.user)
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='pass', performed_by=self.user)
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='fail', performed_by=self.user, results_data={"weight": 105})
        
        response = self.client.get(reverse('quality_control:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.context['fpy'], 66.66666666666666)
        self.assertAlmostEqual(response.context['defect_rate'], 33.33333333333333)
        self.assertEqual(response.context['total_inspections'], 3)

    def test_rca_storage(self):
        # Create a log that fails and triggers NCR
        log = InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='fail', performed_by=self.user)
        ncr = NonConformanceReport.objects.get(inspection_log=log)
        
        # Update NCR with RCA data
        rca_data = {"whys": ["Why 1", "Why 2", "Why 3"]}
        response = self.client.post(reverse('quality_control:ncr_update', args=[ncr.pk]), {
            'root_cause': "Root cause found",
            'action_taken': "rework",
            'rca_type': "5_whys",
            'rca_data': json.dumps(rca_data),
            'resolved_at': ""
        })
        self.assertEqual(response.status_code, 302)
        ncr.refresh_from_db()
        self.assertEqual(ncr.rca_type, "5_whys")
        self.assertEqual(ncr.rca_data, rca_data)

    def test_chart_data_api(self):
        # Create logs with numerical data
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='pass', performed_by=self.user, results_data={"weight": 100})
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='pass', performed_by=self.user, results_data={"weight": 102})
        InspectionLog.objects.create(tenant=self.tenant, rule=self.rule, status='pass', performed_by=self.user, results_data={"weight": 98})
        
        response = self.client.get(reverse('quality_control:chart_data_api') + f'?rule_id={self.rule.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']), 3)
        self.assertEqual(data['stats']['mean'], 100)
        self.assertIn('ucl', data['stats'])
        self.assertIn('lcl', data['stats'])
