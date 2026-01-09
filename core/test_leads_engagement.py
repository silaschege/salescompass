import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from tenants.models import Tenant
from django.contrib.auth import get_user_model
from leads.models import Lead
from engagement.models import EngagementEvent
from django.db import transaction

User = get_user_model()

def run_test():
    try:
        with transaction.atomic():
            # Create test data
            import uuid
            suffix = str(uuid.uuid4())[:8]
            tenant = Tenant.objects.create(name=f'Test Tenant {suffix}', slug=f'test-tenant-{suffix}')
            user = User.objects.create_user(
                username=f'testuser_{suffix}', 
                email='test@test.com', 
                password='password', 
                tenant_id=tenant.id
            )
            
            print("Creating Lead...")
            lead = Lead.objects.create(
                tenant_id=tenant.id,
                first_name='Test',
                last_name='Engagement',
                email='test@engagement.com',
                company='Test Co',
                owner=user,
                lead_source='web'
            )
            
            # Check lead created event
            event_created = EngagementEvent.objects.filter(lead=lead, event_type='lead_created').exists()
            print(f"Lead created event exists: {event_created}")
            
            if event_created:
                event = EngagementEvent.objects.get(lead=lead, event_type='lead_created')
                print(f"Event Title: {event.title}")
                print(f"Engagement Score: {event.engagement_score}")
            
            # Update status
            print("\nUpdating Lead status to 'qualified'...")
            lead.status = 'qualified'
            lead.save()
            
            event_status = EngagementEvent.objects.filter(lead=lead, event_type='lead_qualified').exists()
            print(f"Lead qualified event exists: {event_status}")
            
            # Update score significantly
            print("\nUpdating Lead score by 30 points...")
            lead.lead_score += 30
            lead.save()
            
            event_score = EngagementEvent.objects.filter(lead=lead, event_type='lead_score_changed').exists()
            print(f"Lead score changed event exists: {event_score}")
            
            # ROLLBACK to keep DB clean
            print("\nRolling back transaction...")
            raise Exception("Force Rollback")
    except Exception as e:
        if str(e) != "Force Rollback":
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
