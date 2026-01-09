import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
from .models import Subscription, Plan

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
        
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    return HttpResponse(status=200)


def handle_checkout_session_completed(session):
    """
    Provision subscription after successful checkout.
    """
    # Use the correct field name for tenant reference
    tenant_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
     
    if not tenant_id:
        return
        
    try:
        from tenants.models import Tenant
        from core.models import User
        
        # Get the tenant
        tenant = Tenant.objects.get(id=tenant_id)
        
        # In a real flow, we might look up the plan from metadata
        plan_id = session.get('metadata', {}).get('plan_id')
        if plan_id:
            try:
                plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                plan = Plan.objects.filter(is_active=True).first()  # fallback
        else:
            plan = Plan.objects.filter(is_active=True).first()  # fallback
        
        # Get a user associated with this tenant (e.g., the first admin user)
        user = User.objects.filter(tenant=tenant).first()
        
        if not plan or not user:
            return
        
        # Create or update subscription
        subscription, created = Subscription.objects.get_or_create(
            tenant=tenant,
            user=user,
            defaults={'subscription_plan': plan}
        )
        
        # Update subscription details
        subscription.stripe_customer_id = stripe_customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.status = 'active'
        subscription.subscription_is_active = True
        subscription.save()
        
    except Exception as e:
        print(f"Error handling checkout session: {e}")



def handle_subscription_updated(stripe_sub):
    """
    Update local subscription status when changed in Stripe.
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        
        # Map Stripe status to our status choices
        status_mapping = {
            'active': 'active',
            'trialing': 'trialing',
            'past_due': 'past_due',
            'canceled': 'canceled',
            'unpaid': 'past_due',
            'incomplete': 'incomplete'
        }
        
        mapped_status = status_mapping.get(stripe_sub['status'], 'active')
        
        subscription.status = mapped_status
        subscription.subscription_is_active = stripe_sub['status'] in ['active', 'trialing']
        
        if 'current_period_start' in stripe_sub:
            subscription.start_date = datetime.fromtimestamp(stripe_sub['current_period_start'], tz=timezone.utc)
        if 'current_period_end' in stripe_sub:
            subscription.end_date = datetime.fromtimestamp(stripe_sub['current_period_end'], tz=timezone.utc)
        
        if 'trial_end' in stripe_sub and stripe_sub['trial_end']:
            subscription.subscription_trial_end_date = datetime.fromtimestamp(
                stripe_sub['trial_end'], 
                tz=timezone.utc
            )
        
        subscription.save()
        
    except Subscription.DoesNotExist:
        print(f"Subscription with stripe_subscription_id {stripe_sub['id']} not found")
    except Exception as e:
        print(f"Error handling subscription update: {e}")


def handle_subscription_deleted(stripe_sub):
    """
    Handle subscription cancellation.
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        subscription.status = 'canceled'
        subscription.subscription_is_active = False
        subscription.save()
    except Subscription.DoesNotExist:
        print(f"Subscription with stripe_subscription_id {stripe_sub['id']} not found")
