import os
import django
from datetime import date, timedelta
import sys

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/replit/git/salescompass/core')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from core.models import User
from products.models import Product
from sales.models import Sale, SalesPerformanceMetric
from sales.services import calculate_sales_metrics, aggregate_and_store_metrics

def verify():
    print("Starting Sales Analytics Verification...")
    
    # 1. Setup Data
    try:
        from tenants.models import Tenant
        tenant, _ = Tenant.objects.get_or_create(
            name="Verification Tenant", 
            defaults={'subdomain': 'verify', 'slug': 'verify-tenant'}
        )
        
        user = User.objects.first()
        if not user:
            print("No user found. Create a superuser first.")
            return

        # Assign tenant to user for testing
        if not hasattr(user, 'tenant') or not user.tenant:
            user.tenant = tenant
            user.save()
            
        # Ensure we have a product and account
        product, _ = Product.objects.get_or_create(
            product_name="Test Product", 
            tenant=tenant,
            defaults={'base_price': 100.00, 'pricing_model': 'flat'}
        )
        
        # Determine the correct model for 'Account'
        # In sales/models.py: from core.models import User as Account
        account = user # Since Account IS User in that model definition
        
        # Create Sales
        today = date.today()
        Sale.objects.create(
            account=account,
            product=product,
            sales_rep=user,
            amount=1000.00,
            sale_date=today,
            quantity=1
        )
        Sale.objects.create(
            account=account,
            product=product,
            sales_rep=user,
            amount=500.00,
            sale_date=today - timedelta(days=2),
            quantity=1
        )
        
        print(f"Created sales for user {user.email}")
        
    except Exception as e:
        print(f"Error setting up data: {e}")
        # Proceeding to calculation might fail but try
        
    # 2. Test Calculation
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        metrics = calculate_sales_metrics(start_date, end_date)
        print("\nCalculated Metrics (Organization):")
        print(metrics)
        
        if metrics['total_revenue'] >= 1500.0:
            print("PASS: Revenue calculation looks correct.")
        else:
            print("FAIL: Revenue calculation mismatch.")
            
    except Exception as e:
        print(f"Error calculating metrics: {e}")

    # 3. Test Aggregation Storage
    try:
        print("\nRunning Aggregation...")
        aggregate_and_store_metrics(date=date.today())
        
        metric_count = SalesPerformanceMetric.objects.filter(date=date.today()).count()
        print(f"Stored {metric_count} metrics for today.")
        
        if metric_count > 0:
            print("PASS: Metrics stored successfully.")
        else:
            print("FAIL: No metrics stored.")
            
    except Exception as e:
        print(f"Error aggregating metrics: {e}")

if __name__ == '__main__':
    verify()
