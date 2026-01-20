import os
import django
from django.test import RequestFactory, Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.models import User
from dashboard.models import DashboardConfig
from dashboard.context_processors import user_dashboards

def verify_context_processor():
    # Setup user
    user, _ = User.objects.get_or_create(username='verify_dash_cp', email='verify_dash_cp@example.com')
    user.set_password('password')
    user.save()
    
    # Create dashboard
    dash, _ = DashboardConfig.objects.get_or_create(
        user=user,
        dashboard_name='Test Dashboard'
    )
    
    # Setup request
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # Call context processor
    try:
        context = user_dashboards(request)
        print("Context processor executed successfully.")
        print(f"User dashboards in context: {context.get('user_dashboards')}")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == '__main__':
    verify_context_processor()
