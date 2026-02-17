import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass')
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

try:
    from ml_models.revenue.forecasting.inference import predict_forecast_for_opportunities
    print("Import successful!")
    
    # Mock data
    class MockOpp:
        amount = Decimal('100.00')
        probability = 0.5
        
    result = predict_forecast_for_opportunities([MockOpp()])
    print(f"Result: {result}")
    
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"Error: {e}")
