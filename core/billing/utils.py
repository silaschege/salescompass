"""
Business logic utilities for the billing module.
Provides helper functions for subscription management, pricing calculations,
invoice generation, and payment processing.
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from .models import (
    Plan, Subscription, Invoice, Payment, 
    CreditAdjustment, PaymentMethod, PaymentProviderConfig
)


# ============================================================================
# Subscription Utilities
# ============================================================================

def get_active_subscriptions(tenant_id=None):
    """
    Get all active subscriptions, optionally filtered by tenant.
    
    Args:
        tenant_id: Optional tenant ID to filter by
    
    Returns:
        QuerySet of active subscriptions
    """
    qs = Subscription.objects.filter(status__in=['active', 'trialing'])
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    return qs



def calculate_mrr():
    """
    Calculate total Monthly Recurring Revenue across all active subscriptions.
    
    Returns:
        Decimal: Total MRR
    """
    active_subs = get_active_subscriptions()
    total_mrr = Decimal('0.00')
    
    for sub in active_subs:
        if sub.subscription_plan:
            total_mrr += sub.subscription_plan.price
    
    return total_mrr




def calculate_arr():
    """
    Calculate Annual Recurring Revenue.
    
    Returns:
        Decimal: Total ARR (MRR * 12)
    """
    return calculate_mrr() * 12



def get_subscription_health_score(subscription):
    """
    Calculate a health score for a subscription (0-100).
    Based on payment history, overdue invoices, etc.
    
    Args:
        subscription: Subscription instance
    
    Returns:
        int: Health score (0-100)
    """
    score = 100
    
    # Deduct points for past due status
    if subscription.status == 'past_due':
        score -= 30
    elif subscription.status == 'canceled':
        return 0
    
    # Check for overdue invoices
    overdue_count = Invoice.objects.filter(
        subscription=subscription,
        status__in=['open', 'overdue'],
        due_date__lt=timezone.now().date()
    ).count()
    score -= (overdue_count * 10)
    
    # Check for failed payments
    failed_payments = Payment.objects.filter(
        invoice__subscription=subscription,
        status='failed'
    ).count()
    score -= (failed_payments * 5)
    
    return max(0, min(100, score))







def check_usage_limits(tenant_id, subscription):
    """
    Check if tenant is within their plan limits.
    
    Args:
        tenant_id: Tenant ID
        subscription: Subscription instance
    
    Returns:
        dict: Limit check results
    """
    if not subscription.subscription_plan:
        return {
            'within_limits': False,
            'warnings': ['No plan associated with subscription']
        }
    
    # This is a simplified version - you'd integrate with actual usage tracking
    return {
        'within_limits': True,
        'user_limit': subscription.subscription_plan.max_users,
        'storage_limit_gb': subscription.subscription_plan.storage_limit,
        'api_calls_limit': subscription.subscription_plan.api_calls_limit,
        'has_reports': subscription.subscription_plan.has_reports,
        'has_custom_fields': subscription.subscription_plan.has_custom_fields,
        'has_integrations': subscription.subscription_plan.has_integrations,
        'warnings': []
    }


def get_upgrade_path(current_plan):
    """
    Get recommended upgrade path from current plan.
    
    Args:
        current_plan: Current Plan instance
    
    Returns:
        list: List of recommended upgrade plans
    """
    # Simple implementation based on price - you could enhance this logic
    higher_plans = Plan.objects.filter(
        price__gt=current_plan.price,
        is_active=True
    ).order_by('price')
    
    return higher_plans




# ============================================================================
# Invoice Utilities
# ============================================================================


def generate_invoice_for_subscription(subscription, due_days=7):
    """
    Generate a new invoice for a subscription.
    
    Args:
        subscription: Subscription instance
        due_days: Number of days until invoice is due
    
    Returns:
        Invoice instance
    """
    from django.utils import timezone
    from django.db.models import Max
    
    due_date = timezone.now().date() + timedelta(days=due_days)
    
    # Generate unique invoice number
    last_invoice = Invoice.objects.filter(tenant=subscription.tenant).aggregate(Max('invoice_number'))
    last_number = last_invoice['invoice_number__max']
    
    if last_number:
        # Extract the numeric part and increment
        import re
        match = re.search(r'(\d+)$', str(last_number))
        if match:
            next_number = int(match.group(1)) + 1
        else:
            next_number = 1
    else:
        next_number = 1
    
    invoice_number = f"INV-{next_number:06d}"
    
    # Create the invoice
    invoice = Invoice.objects.create(
        tenant=subscription.tenant,
        invoice_number=invoice_number,
        subscription=subscription,
        amount=subscription.subscription_plan.price,
        due_date=due_date,
        status='draft'
    )
    
    # Set status to open
    invoice.status = 'open'
    invoice.save()
    
    return invoice


def calculate_outstanding_balance(tenant_id):
    """
    Calculate total outstanding balance for a tenant.
    
    Args:
        tenant_id: Tenant ID
    
    Returns:
        Decimal: Total outstanding amount
    """
    from tenants.models import Tenant
    from django.db.models import Sum
    
    total = Invoice.objects.filter(
        tenant_id=tenant_id,
        status__in=['draft', 'open', 'overdue']
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return total



def get_overdue_invoices(tenant_id=None):
    """
    Get all overdue invoices.
    
    Args:
        tenant_id: Optional tenant ID to filter by
    
    Returns:
        QuerySet of overdue invoices
    """
    qs = Invoice.objects.filter(
        status__in=['open', 'overdue'],
        due_date__lt=timezone.now().date()
    )
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    return qs






def apply_credit_to_invoice(invoice, credit_adjustment):
    """
    Apply a credit adjustment to an invoice.
    
    Args:
        invoice: Invoice instance
        credit_adjustment: CreditAdjustment instance
    
    Returns:
        bool: Success status
    """
    if credit_adjustment.amount >= invoice.amount:
        invoice.status = 'paid'
        invoice.save()
        return True
    else:
        # For partial credit, we might want to create a new adjusted invoice
        # For now, we'll just note the credit application
        return False

# ============================================================================
# Payment Utilities
# ============================================================================



def process_payment(invoice, amount, provider='stripe', payment_method_id=None, **kwargs):
    """
    Process a payment for an invoice.
    
    Args:
        invoice: Invoice instance
        amount: Payment amount
        provider: Payment provider name
        payment_method_id: Optional payment method ID
        **kwargs: Additional provider-specific parameters
    
    Returns:
        Payment instance
    """
    from .models import PaymentMethod
    
    # Get the payment method if provided
    payment_method = None
    if payment_method_id:
        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id, tenant=invoice.tenant)
        except PaymentMethod.DoesNotExist:
            # If payment method doesn't exist, we'll continue without it
            pass
    
    payment = Payment.objects.create(
        tenant=invoice.tenant,
        invoice=invoice,
        amount=amount,
        payment_method=payment_method,  # Can be None if not provided
        status='succeeded',
        stripe_payment_intent_id=kwargs.get('transaction_id', ''),
        transaction_id=kwargs.get('transaction_id', ''),
        processed_at=timezone.now()
    )
    
    # Mark invoice as paid if full amount
    if amount >= invoice.amount:
        invoice.status = 'paid'
        invoice.save()
    
    return payment



def refund_payment(payment, amount=None, reason=''):
    """
    Refund a payment.
    
    Args:
        payment: Payment instance
        amount: Amount to refund (None for full refund)
        reason: Reason for refund
    
    Returns:
        Payment instance (refund record)
    """
    if amount is None:
        amount = payment.amount
    
    if amount > payment.amount:
        raise ValueError("Refund amount cannot exceed payment amount")
    
    # Create refund payment record
    refund = Payment.objects.create(
        invoice=payment.invoice,
        amount=-amount,  # Negative amount for refund
        provider=payment.provider,
        status='refunded',
        metadata={'original_payment_id': payment.id, 'reason': reason}
    )
    
    return refund


def get_payment_methods_for_tenant(tenant_id, active_only=True):
    """
    Get all payment methods for a tenant.
    
    Args:
        tenant_id: Tenant ID
        active_only: Only return active payment methods
    
    Returns:
        QuerySet of PaymentMethod instances
    """
    qs = PaymentMethod.objects.filter(tenant_id=tenant_id)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs


def get_available_payment_providers(tenant_id=None):
    """
    Get available payment providers.
    
    Args:
        tenant_id: Optional tenant ID to get tenant-specific providers
    
    Returns:
        QuerySet of PaymentProviderConfig instances
    """
    # Get globally active providers
    providers = PaymentProviderConfig.objects.filter(is_active=True)
    
    # TODO: Filter based on tenant configuration if tenant_id provided
    
    return providers


# ============================================================================
# Analytics Utilities
# ============================================================================



def get_revenue_metrics(start_date=None, end_date=None):
    """
    Calculate revenue metrics for a date range.
    
    Args:
        start_date: Start date (defaults to beginning of current month)
        end_date: End date (defaults to today)
    
    Returns:
        dict: Revenue metrics
    """
    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    if not end_date:
        end_date = timezone.now().date()
    
    # Get paid invoices in range
    invoices = Invoice.objects.filter(
        status='paid',
        invoice_created_at__date__gte=start_date,
        invoice_created_at__date__lte=end_date
    )
    
    total_revenue = invoices.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    invoice_count = invoices.count()
    
    # Get successful payments
    payments = Payment.objects.filter(
        status='succeeded',
        payment_created_at__date__gte=start_date,
        payment_created_at__date__lte=end_date
    )
    payment_count = payments.count()
    
    return {
        'total_revenue': total_revenue,
        'invoice_count': invoice_count,
        'payment_count': payment_count,
        'average_invoice_value': total_revenue / invoice_count if invoice_count > 0 else Decimal('0.00'),
        'period_start': start_date,
        'period_end': end_date
    }


 


def get_churn_metrics():
    """
    Calculate churn metrics.
    
    Returns:
        dict: Churn metrics
    """
    total_subs = Subscription.objects.count()
    active_subs = Subscription.objects.filter(subscription_is_active=True).count()
    canceled_subs = Subscription.objects.filter(status='canceled').count()
    
    # Canceled in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_cancellations = Subscription.objects.filter(
        status='canceled',
        subscription_updated_at__gte=thirty_days_ago
    ).count()
    
    churn_rate = (recent_cancellations / active_subs * 100) if active_subs > 0 else 0
    
    return {
        'total_subscriptions': total_subs,
        'active_subscriptions': active_subs,
        'canceled_subscriptions': canceled_subs,
        'monthly_churn_rate': round(churn_rate, 2),
        'recent_cancellations': recent_cancellations
    }


def get_ltv_estimate(subscription):
    """
    Estimate Lifetime Value (LTV) for a subscription.
    
    Args:
        subscription: Subscription instance
    
    Returns:
        Decimal: Estimated LTV
    """
    if not subscription.subscription_plan:
        return Decimal('0.00')
    
    # Simple LTV calculation: Monthly price * Average customer lifetime
    # Assuming average lifetime of 24 months (adjust based on your data)
    average_lifetime_months = 24
    monthly_value = subscription.subscription_plan.price
    
    return monthly_value * average_lifetime_months


 
# ============================================================================
# Proration Utilities
# ============================================================================


def calculate_detailed_proration(subscription, new_plan, effective_date=None):
    """
    Calculate detailed proration for a plan change.
    
    Args:
        subscription: Current subscription
        new_plan: New plan to switch to
        effective_date: When the change takes effect (default: now)
    
    Returns:
        dict: Detailed proration breakdown
    """
    if not effective_date:
        effective_date = timezone.now()
    
    if not hasattr(subscription, 'current_period_end') or not subscription.current_period_end:
        return {
            'credit_amount': Decimal('0.00'),
            'charge_amount': Decimal('0.00'),
            'net_amount': Decimal('0.00'),
            'error': 'No current period end date available'
        }
    
    # Calculate days
    # Use a default period if no end date is available
    if subscription.current_period_end:
        days_remaining = (subscription.current_period_end.date() - effective_date.date()).days
    else:
        # Default to 30 days if no end date
        days_remaining = 30
    
    days_in_period = 30  # Simplified
    
    # Calculate prorated amounts
    old_daily_rate = subscription.subscription_plan.price / days_in_period if subscription.subscription_plan else Decimal('0.00')
    new_daily_rate = new_plan.price / days_in_period if new_plan else Decimal('0.00')
    
    credit_amount = old_daily_rate * max(0, days_remaining)
    charge_amount = new_daily_rate * max(0, days_remaining)
    net_amount = charge_amount - credit_amount
    
    return {
        'credit_amount': credit_amount,
        'charge_amount': charge_amount,
        'net_amount': net_amount,
        'days_remaining': max(0, days_remaining),
        'old_plan': subscription.subscription_plan.name if subscription.subscription_plan else 'Unknown',
        'new_plan': new_plan.name if new_plan else 'Unknown',
        'effective_date': effective_date
    }



