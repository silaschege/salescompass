from django.test import TestCase
from dashboard.model_introspection import get_available_models, get_model_class, get_model_fields

class ModelIntrospectionTest(TestCase):
    def test_get_available_models_dynamic(self):
        """
        Verify that get_available_models returns models from multiple apps
        and not just a hardcoded list.
        """
        models = get_available_models()
        model_ids = [m['id'] for m in models]
        
        # Check for core apps
        self.assertIn('leads.lead', model_ids)
        self.assertIn('accounts.account', model_ids)
        
        # Check for non-core/obscure apps (proving dynamic discovery)
        # Assuming 'tenants.tenant' or similar exists
        self.assertIn('tenants.tenant', model_ids)
        
        # Verify structure
        first = models[0]
        self.assertIn('id', first)
        self.assertIn('name', first)
        self.assertIn('app_label', first)

    def test_get_model_class_resolution(self):
        """Verify we can resolve a model class from ID string."""
        Lead = get_model_class('leads.lead')
        from leads.models import Lead as ActualLead
        self.assertEqual(Lead, ActualLead)
        
        # Test invalid
        self.assertIsNone(get_model_class('invalid.model'))
        self.assertIsNone(get_model_class('leads.nonexistent'))

    def test_get_model_fields(self):
        """Verify we get fields for a resolved model."""
        fields = get_model_fields('leads.lead')
        field_names = [f['name'] for f in fields]
        
        self.assertIn('first_name', field_names)
        self.assertIn('email', field_names)
        self.assertIn('lead_score', field_names)
        
        # Check metadata
        score_field = next(f for f in fields if f['name'] == 'lead_score')
        self.assertEqual(score_field['type'], 'integer')
        self.assertTrue(score_field['aggregatable'])
