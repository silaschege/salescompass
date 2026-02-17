from .models import Subscription, Invoice as PlatformInvoice, UsageRecord, BillingProfile, Plan
from .stripe_adapter import stripe_adapter
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    @staticmethod
    def create_subscription(user, plan_id, tenant):
        """
        Create a new subscription for a tenant user.
        """
        plan = Plan.objects.get(id=plan_id)
        
        # Create Stripe customer if not exists
        # Assuming we store stripe_customer_id on the user or tenant
        # For simplicity, we'll use the stripe_adapter
        stripe_customer = stripe_adapter.create_customer(
            email=user.email,
            name=user.get_full_name(),
            tenant_id=str(tenant.id)
        )
        
        if not stripe_customer:
            return None
            
        subscription = Subscription.objects.create(
            tenant=tenant,
            user=user,
            subscription_plan=plan,
            status='trialing',
            stripe_customer_id=stripe_customer.id
        )
        
        return subscription

    @staticmethod
    def upgrade_plan(subscription, new_plan_id):
        """
        Upgrade or downgrade a subscription.
        """
        new_plan = Plan.objects.get(id=new_plan_id)
        
        if subscription.stripe_subscription_id:
            # Update stripe
            # In a real app, we'd look up the Stripe Price ID linked to the Plan
            # For now, placeholder 'price_id'
            stripe_adapter.update_subscription(
                subscription.stripe_subscription_id,
                price_id=f"price_{new_plan.id}"
            )
            
        subscription.subscription_plan = new_plan
        subscription.save()
        return subscription

class BillingService:
    @staticmethod
    def generate_invoice(subscription):
        """
        Generate a platform invoice based on plan price and usage.
        """
        # Calculate usage costs
        usage_records = UsageRecord.objects.filter(
            subscription=subscription,
            usage_date__month=timezone.now().month # Simple monthly check
        )
        
        usage_total = Decimal('0.00')
        for record in usage_records:
            # logic to calculate cost per feature key
            pass

        total_amount = subscription.subscription_plan.price + usage_total
        
        invoice = PlatformInvoice.objects.create(
            tenant=subscription.tenant,
            invoice_number=f"PLAT-{timezone.now().strftime('%Y%m%d')}-{subscription.id}",
            subscription=subscription,
            amount=total_amount,
            due_date=timezone.now().date() + timezone.timedelta(days=7),
            status='draft'
        )
        
        return invoice

class PaymentService:
    @staticmethod
    def process_platform_payment(invoice, payment_method_id):
        """
        Process payment for a platform invoice.
        """
        # Logic to call Stripe Charge/PaymentIntent
        return True
