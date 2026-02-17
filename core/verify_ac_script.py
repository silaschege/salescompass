
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salescompass.settings")
django.setup()

from access_control.models import AccessControl

entries = AccessControl.objects.filter(key__startswith='invoicing').values_list('key', flat=True)
print("Invoicing Access Controls:")
for entry in entries:
    print(entry)
