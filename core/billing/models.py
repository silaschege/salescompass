from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

# Legacy choices - kept for backward compatibility during migration
TIER_CHOICES = [
    ('starter', 'Starter'),
    ('pro', 'Pro'),
    ('enterprise', 'Enterprise'),
]

STATUS_CHOICES = [
    ('active', 'Active'),
    ('past_due', 'Past Due'),
    ('canceled', 'Canceled'),
    ('incomplete', 'Incomplete'),
    ('trialing', 'Trialing'),
]

INVOICE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('paid', 'Paid'),
    ('void', 'Void'),
    ('overdue', 'Overdue'),
]

ADJUSTMENT_TYPE_CHOICES = [
    ('credit', 'Credit'),
    ('refund', 'Refund'),
    ('discount', 'Discount'),
]

PROVIDER_CHOICES = [
    ('stripe', 'Stripe'),
    ('mpesa', 'M-Pesa'),
    ('paypal', 'PayPal'),
    ('flutterwave', 'Flutterwave'),
    ('paystack', 'Paystack'),
]

PAYMENT_TYPE_CHOICES = [
    ('card', 'Credit/Debit Card'),
    ('mobile_money', 'Mobile Money'),
    ('bank_account', 'Bank Account'),
    ('wallet', 'Digital Wallet'),
]


class PlanTier(TenantModel):
    """
    Dynamic plan tier values - allows tenant-specific tier tracking.
    """
    tier_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'starter', 'pro'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Starter', 'Pro'
    order = models.IntegerField(default=0)
    tier_is_active = models.BooleanField(default=True, help_text="Whether this tier is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'tier_name']
        unique_together = [('tenant', 'tier_name')]
        verbose_name_plural = 'Plan Tiers'
    
    def __str__(self):
        return self.label


class SubscriptionStatus(TenantModel):
    """
    Dynamic subscription status values - allows tenant-specific status tracking.
    """
    status_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'active', 'canceled'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Active', 'Canceled'
    order = models.IntegerField(default=0)
    status_is_active = models.BooleanField(default=True, help_text="Whether this status is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'status_name']
        unique_together = [('tenant', 'status_name')]
        verbose_name_plural = 'Subscription Statuses'
    
    def __str__(self):
        return self.label


class AdjustmentType(TenantModel):
    """
    Dynamic adjustment type values - allows tenant-specific adjustment tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'credit', 'refund'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Credit', 'Refund'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Adjustment Types'
    
    def __str__(self):
        return self.label


class PaymentProvider(TenantModel):
    """
    Dynamic payment provider values - allows tenant-specific provider tracking.
    """
    provider_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'stripe', 'paypal'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=100)  # e.g., 'Stripe', 'PayPal'
    order = models.IntegerField(default=0)
    provider_is_active = models.BooleanField(default=True, help_text="Whether this provider is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'provider_name']
        unique_together = [('tenant', 'provider_name')]
        verbose_name_plural = 'Payment Providers'
    
    def __str__(self):
        return self.label


class PaymentType(TenantModel):
    """
    Dynamic payment type values - allows tenant-specific payment type tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'card', 'mobile_money'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Credit/Debit Card', 'Mobile Money'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Payment Types'
    
    def __str__(self):
        return self.label


class Plan(TenantModel):
    plan_name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='starter')
    # New dynamic field
    tier_ref = models.ForeignKey(
        PlanTier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='plans',
        help_text="Dynamic tier (replaces tier field)"
    )
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_annually = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    features = models.JSONField(default=list, blank=True, help_text="List of features included in the plan")
    plan_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    plan_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    plan_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.plan_name} ({self.tier})"


class Subscription(TenantModel):
    subscription_plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    # New dynamic field
    status_ref = models.ForeignKey(
        SubscriptionStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subscriptions',
        help_text="Dynamic status (replaces status field)"
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    subscription_trial_end_date = models.DateTimeField(null=True, blank=True, help_text="End date of subscription trial period")  # Renamed from 'trial_end_date' to avoid conflict with base class
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    subscription_is_active = models.BooleanField(default=True) # Renamed from 'is_active' to avoid conflict with base class
    subscription_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    subscription_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.plan_name}"


class Invoice(TenantModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('overdue', 'Overdue'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    issued_date = models.DateField(auto_now_add=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    pdf_url = models.URLField(blank=True)
    invoice_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    invoice_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    invoice_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"


class CreditAdjustment(TenantModel):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='credit_adjustments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_adjustments', null=True, blank=True)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    # New dynamic field
    adjustment_type_ref = models.ForeignKey(
        AdjustmentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='credit_adjustments',
        help_text="Dynamic adjustment type (replaces adjustment_type field)"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_description = models.TextField() # Renamed from 'description' to avoid conflict with base class
    applied_date = models.DateTimeField(auto_now_add=True)
    adjustment_is_active = models.BooleanField(default=True) # Renamed from 'is_active' to avoid conflict with base class
    adjustment_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    adjustment_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.adjustment_type} - {self.amount}"


class PaymentProviderConfig(TenantModel):
    provider_config_name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True, help_text="e.g., 'stripe', 'paypal'")  # Renamed from 'name' to avoid conflict
    # New dynamic field
    name_ref = models.ForeignKey(
        PaymentProvider,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='configs',
        help_text="Dynamic provider (replaces name field)"
    )
    display_name = models.CharField(max_length=100)
    api_key = models.TextField()
    secret_key = models.TextField()
    webhook_secret = models.TextField()
    config_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    config_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    config_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.display_name


class PaymentMethod(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    # New dynamic field
    type_ref = models.ForeignKey(
        PaymentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payment_methods',
        help_text="Dynamic payment type (replaces type field)"
    )
    display_info = models.CharField(
        max_length=100,
        help_text="Masked display info (e.g., '**** 4242', '+254 *** 1234')"
    )
    provider = models.ForeignKey(PaymentProviderConfig, on_delete=models.CASCADE, related_name='payment_methods')
    provider_payment_method_id = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    payment_method_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    method_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    method_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.user.email} - {self.type}: {self.display_info}"


class Payment(TenantModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='payments')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], default='pending')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    payment_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    payment_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    payment_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"Payment for {self.invoice.invoice_number} - {self.status}"
