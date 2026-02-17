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

class PlanTier(TenantModel):
    """
    Dynamic plan tier values - allows tenant-specific tier tracking.
    """
    tier_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'starter', 'pro'")
    label = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    tier_is_active = models.BooleanField(default=True, help_text="Whether this tier is active")
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
    status_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'active', 'canceled'")
    label = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    status_is_active = models.BooleanField(default=True, help_text="Whether this status is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'status_name']
        unique_together = [('tenant', 'status_name')]
        verbose_name_plural = 'Subscription Statuses'
    
    def __str__(self):
        return self.label


class Plan(models.Model):
    """Billing plan model - referenced in Tenant model"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField(default=1)
    storage_limit = models.IntegerField(default=1, help_text="Storage limit in GB")
    api_calls_limit = models.IntegerField(default=1000, help_text="Monthly API call limit")
    has_reports = models.BooleanField(default=False)
    has_custom_fields = models.BooleanField(default=False)
    has_integrations = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    features_config = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Structured configuration of modules and features for this plan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        ordering = ['name']
    
    def __str__(self):
        return self.name

    @property
    def price_monthly(self):
        """Monthly price for the plan."""
        return self.price

    @property
    def price_yearly(self):
        """Yearly price for the plan (monthly price * 12)."""
        return self.price * 12


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
        help_text="Dynamic status (replaces status field)"
    )
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions', help_text="Account associated with this subscription")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    subscription_trial_end_date = models.DateTimeField(null=True, blank=True, help_text="End date of subscription trial period")
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    subscription_is_active = models.BooleanField(default=True)
    subscription_created_at = models.DateTimeField(auto_now_add=True)
    subscription_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.name if self.subscription_plan else 'No Plan'}"

    @property
    def plan(self):
        """Property to access the subscription plan for template compatibility."""
        return self.subscription_plan

    @property
    def current_period_start(self):
        """Property to provide current period start date."""
        return self.start_date

    @property
    def current_period_end(self):
        """Property to provide current period end date."""
        if self.end_date:
            return self.end_date
        from django.utils import timezone
        from datetime import timedelta
        return self.start_date + timedelta(days=30)

    @property
    def price_monthly(self):
        """Monthly price of the subscription based on the plan."""
        if self.subscription_plan:
            return self.subscription_plan.price
        return 0


class PlanFeatureAccess(models.Model):
    """
    Model for defining which features are available for each plan
    """
    plan = models.ForeignKey('billing.Plan', on_delete=models.CASCADE, related_name='feature_access')
    feature_key = models.CharField(max_length=255, help_text="Unique identifier for the feature (e.g., leads_basic, sales_reports)")
    feature_name = models.CharField(max_length=255, help_text="Display name for the feature")
    is_available = models.BooleanField(default=True, help_text="Whether this feature is available for this plan")
    feature_category = models.CharField(max_length=100, help_text="Category of the feature (e.g., leads, sales, engagement)")
    notes = models.TextField(blank=True, help_text="Additional notes about this feature access")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plan Feature Access"
        verbose_name_plural = "Plan Feature Accesses"
        unique_together = ['plan', 'feature_key']
        ordering = ['feature_category', 'feature_name']
    
    def __str__(self):
        return f"{self.feature_name} for {self.plan.name} - {'Available' if self.is_available else 'Not Available'}"
    

class PlanModuleAccess(models.Model):
    """
    Model for defining which modules are available for each plan
    """
    plan = models.ForeignKey('billing.Plan', on_delete=models.CASCADE, related_name='module_access')
    module_name = models.CharField(max_length=100, help_text="Name of the module (e.g., leads, sales, engagement)")
    module_display_name = models.CharField(max_length=255, help_text="Display name for the module")
    is_available = models.BooleanField(default=True, help_text="Whether this module is available for this plan")
    notes = models.TextField(blank=True, help_text="Additional notes about this module access")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plan Module Access"
        verbose_name_plural = "Plan Module Accesses"
        unique_together = ['plan', 'module_name']
        ordering = ['module_display_name']
    
    def __str__(self):
        return f"{self.module_display_name} for {self.plan.name} - {'Available' if self.is_available else 'Not Available'}"

# --- Moved from core/invoicing/models.py ---

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


class AdjustmentType(TenantModel):
    """
    Dynamic adjustment type values - allows tenant-specific adjustment tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'credit', 'refund'")
    label = models.CharField(max_length=50)  # e.g., 'Credit', 'Refund'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'billing_adjustmenttype'
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Adjustment Types'
    
    def __str__(self):
        return self.label


class PaymentProvider(TenantModel):
    """
    Dynamic payment provider values - allows tenant-specific provider tracking.
    """
    provider_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'stripe', 'paypal'")
    label = models.CharField(max_length=100)  # e.g., 'Stripe', 'PayPal'
    order = models.IntegerField(default=0)
    provider_is_active = models.BooleanField(default=True, help_text="Whether this provider is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'billing_paymentprovider'
        ordering = ['order', 'provider_name']
        unique_together = [('tenant', 'provider_name')]
        verbose_name_plural = 'Payment Providers'
    
    def __str__(self):
        return self.label


class PaymentType(TenantModel):
    """
    Dynamic payment type values - allows tenant-specific payment type tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'card', 'mobile_money'")
    label = models.CharField(max_length=50)  # e.g., 'Credit/Debit Card', 'Mobile Money'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")
    is_system = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'billing_paymenttype'
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Payment Types'
    
    def __str__(self):
        return self.label


class PaymentProviderConfig(TenantModel):
    provider_config_name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True, help_text="e.g., 'stripe', 'paypal'")
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
    config_is_active = models.BooleanField(default=True)
    config_created_at = models.DateTimeField(auto_now_add=True)
    config_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_paymentproviderconfig'
    
    def __str__(self):
        return self.display_name


class PaymentMethod(TenantModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
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
    payment_method_is_active = models.BooleanField(default=True)
    method_created_at = models.DateTimeField(auto_now_add=True)
    method_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_paymentmethod'
    
    def __str__(self):
        return f"{self.user.email} - {self.type}: {self.display_info}"


class Invoice(TenantModel):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='billing_invoices')
    STATUS_CHOICES = INVOICE_STATUS_CHOICES
    
    invoice_number = models.CharField(max_length=50, unique=True)
    subscription = models.ForeignKey('billing.Subscription', on_delete=models.CASCADE, related_name='invoices')
    account = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', help_text="Account associated with this invoice")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    issued_date = models.DateField(auto_now_add=True)
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    pdf_url = models.URLField(blank=True)
    invoice_is_active = models.BooleanField(default=True)
    invoice_created_at = models.DateTimeField(auto_now_add=True)
    invoice_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_invoice'

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"


class CreditAdjustment(TenantModel):
    subscription = models.ForeignKey('billing.Subscription', on_delete=models.CASCADE, related_name='credit_adjustments')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='credit_adjustments', null=True, blank=True)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    adjustment_type_ref = models.ForeignKey(
        AdjustmentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='credit_adjustments',
        help_text="Dynamic adjustment type (replaces adjustment_type field)"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_description = models.TextField()
    applied_date = models.DateTimeField(auto_now_add=True)
    adjustment_is_active = models.BooleanField(default=True)
    adjustment_created_at = models.DateTimeField(auto_now_add=True)
    adjustment_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_creditadjustment'
    
    def __str__(self):
        return f"{self.adjustment_type} - {self.amount}"


class Payment(TenantModel):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='billing_payments')
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
    payment_is_active = models.BooleanField(default=True)
    payment_created_at = models.DateTimeField(auto_now_add=True)
    payment_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_payment'


class UsageRecord(TenantModel, TimeStampedModel):
    """
    Track usage of metered features for billing purposes.
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_records')
    feature_key = models.CharField(max_length=255, help_text="Feature being metered (e.g. 'api_calls', 'storage_gb')")
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    usage_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-usage_date']
        
    def __str__(self):
        return f"{self.subscription} - {self.feature_key}: {self.quantity}"


class BillingProfile(TenantModel, TimeStampedModel):
    """
    Tax and billing information for the Tenant as a customer of the Platform.
    """
    company_name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=50, blank=True)
    billing_email = models.EmailField()
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Kenya')

    def __str__(self):
        return f"Billing Profile: {self.company_name} ({self.tenant})"


