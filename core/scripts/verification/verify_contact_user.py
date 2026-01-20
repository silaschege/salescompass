import os
import django
import sys

# Set up Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from accounts.models import Contact
from core.models import User

def verify_changes():
    print("Verifying Contact and User model changes...")
    
    # 1. Verify Contact Fields
    print("\n--- Verifying Contact Fields ---")
    try:
        # Check if fields exist on the model class
        fields = [f.name for f in Contact._meta.get_fields()]
        required_fields = ['esg_influence', 'role', 'communication_preference', 'is_primary']
        
        missing = [f for f in required_fields if f not in fields]
        
        if missing:
            print(f"FAILED: Missing fields on Contact model: {missing}")
        else:
            print("SUCCESS: All required fields found on Contact model.")
            
            # Verify choices
            print(f"ESG Choices: {Contact.ESG_INFLUENCE_CHOICES}")
            print(f"Comm Pref Choices: {Contact.COMMUNICATION_PREFERENCE_CHOICES}")
            
    except Exception as e:
        print(f"ERROR verifying Contact: {e}")

    # 2. Verify User Methods
    print("\n--- Verifying User Methods ---")
    try:
        user = User(first_name="Jane", last_name="Doe", email="jane@example.com")
        
        # Test get_full_name
        if hasattr(user, 'get_full_name'):
            full_name = user.get_full_name()
            print(f"get_full_name(): '{full_name}'")
            if full_name == "Jane Doe":
                print("SUCCESS: get_full_name() works as expected.")
            else:
                print(f"FAILED: get_full_name() returned '{full_name}'")
        else:
            print("FAILED: get_full_name method missing.")

        # Test get_short_name
        if hasattr(user, 'get_short_name'):
            short_name = user.get_short_name()
            print(f"get_short_name(): '{short_name}'")
            if short_name == "Jane":
                 print("SUCCESS: get_short_name() works as expected.")
            else:
                print(f"FAILED: get_short_name() returned '{short_name}'")
        else:
            print("FAILED: get_short_name method missing.")

    except Exception as e:
         print(f"ERROR verifying User: {e}")

if __name__ == "__main__":
    verify_changes()
