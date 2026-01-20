import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from sCompass.celery import app
from automation.tasks import evaluate_assignment_rules

def test_celery_config():
    print(f"Broker URL: {app.conf.broker_url}")
    print(f"Timezone: {app.conf.timezone}")
    
    # Enable eager mode for testing without running worker
    app.conf.task_always_eager = True
    
    print("Testing task execution...")
    try:
        # We pass dummy values since we just want to see if it dispatches
        result = evaluate_assignment_rules.delay('leads', 999)
        print(f"Task dispatched successfully. Result: {result.get()}")
    except Exception as e:
        print(f"Task execution failed: {e}")

if __name__ == "__main__":
    test_celery_config()
