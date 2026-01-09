from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from billing.models import Plan, PlanModuleAccess, PlanFeatureAccess
from billing.plan_access_service import PlanAccessService
from tenants.models import Tenant

User = get_user_model()

class PlanAccessTest(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name="Test Pro",
            price=99.99,
            features_config={
                "leads": {
                    "enabled": True,
                    "features": {"lead_scoring": True}
                },
                "sales": {
                    "enabled": False,
                    "features": {}
                }
            }
        )
        # Signal should have synced the records automatically
        
    def test_signal_sync(self):
        """Verify that saving a plan syncs module and feature access records"""
        self.assertTrue(PlanModuleAccess.objects.filter(plan=self.plan, module_name="leads", is_available=True).exists())
        self.assertTrue(PlanModuleAccess.objects.filter(plan=self.plan, module_name="sales", is_available=False).exists())
        self.assertTrue(PlanFeatureAccess.objects.filter(plan=self.plan, feature_key="lead_scoring", is_available=True).exists())

    def test_service_access_checks(self):
        """Verify the PlanAccessService correctly checks access"""
        self.assertTrue(PlanAccessService.get_module_access(self.plan, "leads"))
        self.assertFalse(PlanAccessService.get_module_access(self.plan, "sales"))
        self.assertTrue(PlanAccessService.get_feature_access(self.plan, "leads", "lead_scoring"))
        # Feature access should be false if module is disabled
        self.assertFalse(PlanAccessService.get_feature_access(self.plan, "sales", "any_feature"))

    def test_fallback_logic(self):
        """Test fallback to JSON config if records are missing"""
        # Delete records to force fallback
        PlanModuleAccess.objects.all().delete()
        self.assertTrue(PlanAccessService.get_module_access(self.plan, "leads"))
