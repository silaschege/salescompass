
import os
import django
from django.urls import reverse, NoReverseMatch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.salescompass.settings")
django.setup()

def verify_reverse_match():
    try:
        url = reverse('conversation_list')
        print(f"SUCCESS: 'conversation_list' resolved to '{url}'")
    except NoReverseMatch as e:
        print(f"FAILURE: Could not resolve 'conversation_list'. Error: {e}")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")

    try:
        url = reverse('communication:unified_inbox')
        print(f"SUCCESS: 'communication:unified_inbox' resolved to '{url}'")
    except NoReverseMatch as e:
        print(f"FAILURE: Could not resolve 'communication:unified_inbox'. Error: {e}")

if __name__ == "__main__":
    verify_reverse_match()
