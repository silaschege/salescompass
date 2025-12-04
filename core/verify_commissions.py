import os
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

User = get_user_model()

def verify_commissions():
    print("Starting verification...")
    
    # Create test user
    username = 'testuser_commissions'
    password = 'testpassword123'
    email = 'test@example.com'
    
    # Ensure Role exists
    from core.models import Role
    role, _ = Role.objects.get_or_create(name='sales')
    
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        user.set_password(password)
        user.role = role
        user.save()
    else:
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role
        user.save()
    
    print(f"User {username} created/updated.")
    
    client = Client()
    login_success = client.login(email=email, password=password)
    
    if login_success:
        print("Login successful.")
    else:
        print("Login failed.")
        return

    # Verify Commissions List Page
    try:
        response = client.get('/commissions/')
        if response.status_code == 200:
            print("SUCCESS: /commissions/ returned 200 OK.")
            if 'Commissions' in str(response.content):
                print("SUCCESS: 'Commissions' text found in response.")
            else:
                print("WARNING: 'Commissions' text NOT found in response.")
        else:
            print(f"FAILURE: /commissions/ returned {response.status_code}.")
    except Exception as e:
        print(f"ERROR accessing /commissions/: {e}")

    # Verify App Selection Page
    try:
        # Assuming app selection is at / or /apps/ or check core.urls
        # Let's try to find the URL for app selection.
        # Based on previous context, it might be 'app_selection' name in core urls.
        try:
            url = reverse('core:app_selection')
        except:
            try:
                url = reverse('app_selection')
            except:
                url = '/' # Fallback
        
        print(f"Checking App Selection at {url}...")
        response = client.get(url)
        if response.status_code == 200:
            if 'commissions' in str(response.content).lower():
                print("SUCCESS: 'commissions' link found in App Selection page.")
            else:
                print("WARNING: 'commissions' link NOT found in App Selection page.")
        else:
            print(f"FAILURE: App Selection page returned {response.status_code}.")
            
    except Exception as e:
        print(f"ERROR accessing App Selection: {e}")

    # Verify Dashboard Sidebar
    try:
        # Dashboard usually at /dashboard/
        response = client.get('/dashboard/')
        if response.status_code == 200:
            if 'commissions' in str(response.content).lower():
                print("SUCCESS: 'commissions' link found in Dashboard.")
            else:
                print("WARNING: 'commissions' link NOT found in Dashboard.")
        else:
            print(f"FAILURE: Dashboard returned {response.status_code}.")
    except Exception as e:
        print(f"ERROR accessing Dashboard: {e}")

if __name__ == '__main__':
    verify_commissions()
