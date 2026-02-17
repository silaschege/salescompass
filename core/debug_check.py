
import os
import sys
import django
from django.core.management import call_command

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')

try:
    django.setup()
    print("Django setup success")
    call_command('check')
    print("Check passed")
except Exception as e:
    print("Check failed with error:")
    import traceback
    traceback.print_exc()
