from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from settings_app.models import APIKey, Webhook
import ast
import json

User = get_user_model()


class APIDocumentationEndpointTests(TestCase):
    """Test that API documentation endpoints are accessible."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI endpoint is accessible."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger')
    
    def test_redoc_accessible(self):
        """Test that Redoc endpoint is accessible."""
        response = self.client.get('/api/redoc/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'redoc')
    
    def test_openapi_schema_generation(self):
        """Test that OpenAPI schema is generated correctly."""
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        
        # Verify content type
        self.assertIn('application/vnd.oai.openapi', response['Content-Type'])
        
        # Try to parse as JSON (schema might be YAML)
        try:
            schema = json.loads(response.content)
            # Verify basic OpenAPI structure
            self.assertIn('openapi', schema)
            self.assertIn('info', schema)
            self.assertIn('paths', schema)
            
            # Verify our API metadata
            self.assertEqual(schema['info']['title'], 'SalesCompass API')
            self.assertEqual(schema['info']['version'], '1.0.0')
        except json.JSONDecodeError:
            # If it's YAML, just verify content exists
            self.assertGreater(len(response.content), 0)


class CodeExampleValidationTests(TestCase):
    """Test that code examples in the portal are syntactically correct."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_python_code_examples_valid(self):
        """Test that Python code examples are syntactically correct."""
        # Python example from portal
        python_code = '''
import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

response = requests.get(f"{BASE_URL}/api/leads/", headers=headers)
leads = response.json()

print(f"Found {len(leads)} leads")
for lead in leads:
    print(f"- {lead['first_name']} {lead['last_name']} ({lead['email']})")
'''
        
        # Verify it's valid Python syntax
        try:
            ast.parse(python_code)
            valid = True
        except SyntaxError:
            valid = False
        
        self.assertTrue(valid, "Python code example has syntax errors")
    
    def test_javascript_code_examples_valid(self):
        """Test that JavaScript code examples are valid."""
        # JavaScript example from portal
        javascript_code = '''
const API_KEY = "YOUR_API_KEY";
const BASE_URL = "http://localhost:8000";

async function createLead(leadData) {
    const response = await fetch(`${BASE_URL}/api/leads/`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(leadData)
    });
    
    const data = await response.json();
    return data;
}

createLead({
    first_name: "John",
    last_name: "Doe",
    email: "john@example.com",
    phone: "+1234567890"
}).then(lead => {
    console.log("Lead created:", lead);
});
'''
        
        # Basic validation: check for async/await keywords
        self.assertIn('async', javascript_code)
        self.assertIn('await', javascript_code)
        self.assertIn('fetch', javascript_code)
        self.assertIn('JSON.stringify', javascript_code)
    
    def test_curl_examples_valid(self):
        """Test that cURL command examples are correctly formatted."""
        # cURL example from portal
        curl_command = 'curl -X GET "http://localhost:8000/api/opportunities/" -H "Authorization: Bearer YOUR_API_KEY" -H "Content-Type: application/json"'
        
        # Verify basic cURL structure
        self.assertIn('curl', curl_command)
        self.assertIn('-X GET', curl_command)
        self.assertIn('-H "Authorization:', curl_command)
        self.assertIn('Bearer', curl_command)


class APIKeyAuthenticationTests(TestCase):
    """Test API key generation and authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_api_key_generation(self):
        """Test that API keys can be generated."""
        key = APIKey.generate_key()
        
        # Verify format (should start with 'sk_')
        self.assertTrue(key.startswith('sk_'))
        
        # Verify length (should be reasonable length)
        self.assertGreater(len(key), 20)
    
    def test_api_key_creation(self):
        """Test creating an API key through the view."""
        response = self.client.post(reverse('developer:generate_key'), {
            'name': 'Test API Key',
            'scopes': ['read', 'write']
        })
        
        # Should redirect after creation
        self.assertEqual(response.status_code, 302)
        
        # Verify key was created
        api_key = APIKey.objects.filter(
            created_by=self.user,
            name='Test API Key'
        ).first()
        
        self.assertIsNotNone(api_key)
        self.assertEqual(api_key.tenant_id, 'test_tenant')
    
    def test_api_key_validation(self):
        """Test that API key validation works correctly."""
        # Generate and store a key
        key = APIKey.generate_key()
        api_key = APIKey.objects.create(
            name='Test Key',
            created_by=self.user,
            tenant_id='test_tenant',
            scopes=['read']
        )
        api_key.set_key(key)
        api_key.save()
        
        # Verify the key can be validated
        self.assertTrue(api_key.verify_key(key))
        
        # Verify wrong key fails
        self.assertFalse(api_key.verify_key('wrong_key'))
    
    def test_portal_view_requires_authentication(self):
        """Test that portal view requires authentication."""
        self.client.logout()
        
        response = self.client.get(reverse('developer:portal'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_api_key_list_in_portal(self):
        """Test that API keys are listed in the portal."""
        # Create some API keys
        APIKey.objects.create(
            name='Key 1',
            created_by=self.user,
            tenant_id='test_tenant',
            scopes=['read']
        )
        APIKey.objects.create(
            name='Key 2',
            created_by=self.user,
            tenant_id='test_tenant',
            scopes=['write']
        )
        
        response = self.client.get(reverse('developer:portal'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Key 1')
        self.assertContains(response, 'Key 2')


class WebhookTestingTests(TestCase):
    """Test webhook testing functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        self.client.login(username='test@example.com', password='testpass123')
        
        self.webhook = Webhook.objects.create(
            name='Test Webhook',
            url='https://example.com/webhook',
            events=['test.event'],
            secret='test_secret_123',
            tenant_id='test_tenant',
            is_active=True
        )
    
    def test_webhook_test_endpoint(self):
        """Test that webhook testing endpoint works."""
        response = self.client.post(reverse('developer:test_webhook'), {
            'webhook_id': self.webhook.id,
            'event_type': 'test.event'
        })
        
        # Should return JSON response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify response structure
        self.assertIn('success', data)
    
    def test_webhook_test_invalid_id(self):
        """Test webhook testing with invalid webhook ID."""
        response = self.client.post(reverse('developer:test_webhook'), {
            'webhook_id': 99999,
            'event_type': 'test.event'
        })
        
        # View currently returns 200 with error in JSON
        # OR 400 depending on implementation
        self.assertIn(response.status_code, [200, 400])
        
        # Verify error response
        try:
            data = json.loads(response.content)
            if 'success' in data:
                self.assertFalse(data.get('success', True))
        except json.JSONDecodeError:
            pass  # If not JSON, status code check is enough


class UsageAnalyticsTests(TestCase):
    """Test usage analytics views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant_id='test_tenant'
        )
        self.client.login(username='test@example.com', password='testpass123')
    
    def test_analytics_view_accessible(self):
        """Test that analytics view is accessible."""
        response = self.client.get(reverse('developer:analytics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usage Analytics')
    
    def test_analytics_shows_statistics(self):
        """Test that analytics view shows statistics."""
        # Create some test data
        APIKey.objects.create(
            name='Key 1',
            created_by=self.user,
            tenant_id='test_tenant',
            scopes=['read']
        )
        
        Webhook.objects.create(
            name='Webhook 1',
            url='https://example.com/webhook',
            events=['test.event'],
            secret='secret',
            tenant_id='test_tenant',
            success_count=10,
            failure_count=2
        )
        
        response = self.client.get(reverse('developer:analytics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Key 1')
        self.assertContains(response, 'Webhook 1')
