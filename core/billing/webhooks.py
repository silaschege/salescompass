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
    tenant_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
    
    if not tenant_id:
        return
        
    try:
        # Find the subscription placeholder or create new
        # Assuming we might have pre-created a subscription record or we create one now
        # For simplicity, we'll try to get an existing one by tenant_id or create
        
        # In a real flow, we might look up the plan from metadata
        plan_id = session.get('metadata', {}).get('plan_id')
        plan = Plan.objects.get(id=plan_id) if plan_id else Plan.objects.first()
        
        subscription, created = Subscription.objects.get_or_create(
            tenant_id=tenant_id,
            defaults={'plan': plan}
        )
        
        subscription.stripe_customer_id = stripe_customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.status = 'active'
        subscription.save()
        
    except Exception as e:
        print(f"Error handling checkout session: {e}")

def handle_subscription_updated(stripe_sub):
    """
    Update local subscription status when changed in Stripe.
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        
        subscription.status = stripe_sub['status']
        subscription.current_period_start = datetime.fromtimestamp(stripe_sub['current_period_start'], tz=timezone.utc)
        subscription.current_period_end = datetime.fromtimestamp(stripe_sub['current_period_end'], tz=timezone.utc)
        subscription.cancel_at_period_end = stripe_sub['cancel_at_period_end']
        subscription.save()
        
    except Subscription.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error handling subscription update: {e}")

def handle_subscription_deleted(stripe_sub):
    """
    Handle subscription cancellation.
    """
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_sub['id'])
        subscription.status = 'canceled'
        subscription.save()
    except Subscription.DoesNotExist:
        pass
