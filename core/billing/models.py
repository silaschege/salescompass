from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TenantModel, TimeStampedModel
from decimal import Decimal

class Plan(TimeStampedModel):
    """
    SaaS Subscription Plan.
    """
    TIER_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='starter')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)
    
    # Limits
    max_users = models.IntegerField(default=1)
    max_leads = models.IntegerField(default=100)
    max_storage_gb = models.IntegerField(default=1)
    features = models.JSONField(default=list, help_text="List of enabled feature flags")
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    # Pricing Methods
    def get_price(self, interval='monthly'):
        """Get price for billing interval"""
        return self.price_monthly if interval == 'monthly' else self.price_yearly
    
    def calculate_mrr(self):
        """Calculate monthly recurring revenue contribution"""
        return float(self.price_monthly)
    
    def has_feature(self, feature_name):
        """Check if plan includes a specific feature"""
        return feature_name in self.features


class Subscription(TimeStampedModel):
    """
    Tenant Subscription linked to a Plan.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('trialing', 'Trialing'),
    ]
    
    tenant_id = models.CharField(max_length=50, unique=True, db_index=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing')
    
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    # Billing Contact
    billing_email = models.EmailField(blank=True)
    
    def __str__(self):
        return f"{self.tenant_id} - {self.plan.name} ({self.status})"
    
    @property
    def is_valid(self):
        return self.status in ['active', 'trialing']
    
    # Lifecycle Methods
    def upgrade_to(self, new_plan):
        """Upgrade subscription to a new plan"""
        old_plan = self.plan
        self.plan = new_plan
        self.save()
        return {'old_plan': old_plan, 'new_plan': new_plan}
    
    def downgrade_to(self, new_plan):
        """Downgrade subscription to a new plan"""
        return self.upgrade_to(new_plan)  # Same logic, different semantics
    
    def calculate_proration(self, new_plan):
        """Calculate proration amount for plan change"""
        if not self.current_period_end:
            return Decimal('0.00')
        
        now = timezone.now()
        days_remaining = (self.current_period_end - now).days
        days_in_period = 30  # Simplified
        
        unused_amount = (self.plan.price_monthly / days_in_period) * days_remaining
        new_amount = (new_plan.price_monthly / days_in_period) * days_remaining
        
        return new_amount - unused_amount
    
    def cancel(self, immediate=False):
        """Cancel subscription"""
        if immediate:
            self.status = 'canceled'
            self.save()
        else:
            self.cancel_at_period_end = True
            self.save()
    
    def reactivate(self):
        """Reactivate a canceled subscription"""
        self.status = 'active'
        self.cancel_at_period_end = False
        self.save()


class Invoice(TimeStampedModel):
    """
    Invoice for subscription billing
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('overdue', 'Overdue'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    tenant_id = models.CharField(max_length=50, db_index=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.tenant_id}"
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not set
        if not self.invoice_number:
            # Format: INV-YYYYMM-XXXXX
            now = timezone.now()
            prefix = f"INV-{now.strftime('%Y%m')}"
            # Get last invoice for this month
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                # Extract number and increment
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.invoice_number = f"{prefix}-{new_num:05d}"
        
        # Calculate total
        self.total = self.subtotal + self.tax
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        if self.status == 'paid':
            return False
        return timezone.now().date() > self.due_date
    
    def mark_paid(self):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
    
    def void(self):
        """Void the invoice"""
        if self.status == 'paid':
            raise ValueError("Cannot void a paid invoice")
        self.status = 'void'
        self.save()
    
    def finalize(self):
        """Finalize draft invoice and make it open"""
        if self.status == 'draft':
            self.status = 'open'
            self.save()
    
    @classmethod
    def create_from_subscription(cls, subscription, due_date=None):
        """Create an invoice from a subscription"""
        if not due_date:
            due_date = timezone.now().date() + timedelta(days=7)
        
        invoice = cls.objects.create(
            subscription=subscription,
            tenant_id=subscription.tenant_id,
            subtotal=subscription.plan.price_monthly,
            tax=subscription.plan.price_monthly * Decimal('0.00'),  # No tax for now
            due_date=due_date
        )
        
        # Create line item
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=f"{subscription.plan.name} - Monthly Subscription",
            quantity=1,
            unit_price=subscription.plan.price_monthly,
            amount=subscription.plan.price_monthly
        )
        
        return invoice


class InvoiceLineItem(models.Model):
    """
    Line item on an invoice
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"


class Payment(TimeStampedModel):
    """
    Payment transaction record
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Provider tracking (new)
    provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment provider used (stripe, mpesa, paypal, etc.)"
    )
    
    # Legacy Stripe fields (kept for backward compatibility)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Generic provider transaction ID
    provider_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Provider-specific transaction/payment ID"
    )
    
    error_message = models.TextField(blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        provider_info = f" via {self.provider}" if self.provider else ""
        return f"Payment ${self.amount} - {self.status}{provider_info}"


class CreditAdjustment(TimeStampedModel):
    """
    Credit adjustments and refunds
    """
    ADJUSTMENT_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('refund', 'Refund'),
        ('discount', 'Discount'),
    ]
    
    tenant_id = models.CharField(max_length=50, db_index=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='adjustments', null=True, blank=True)
    
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    applied_to_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.adjustment_type.title()} ${self.amount} - {self.tenant_id}"


# ============================================================================
# Three-Tier Payment Architecture Models
# ============================================================================

class PaymentProviderConfig(TimeStampedModel):
    """
    Platform-level payment provider configuration.
    Managed by superadmins to enable payment providers globally.
    """
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('mpesa', 'M-Pesa'),
        ('paypal', 'PayPal'),
        ('flutterwave', 'Flutterwave'),
        ('paystack', 'Paystack'),
    ]
    
    name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False, help_text="Enable this provider globally")
    
    # Encrypted configuration (API keys, secrets, etc.)
    config = models.JSONField(
        default=dict,
        help_text="Provider-specific configuration (API keys, secrets). Should be encrypted in production."
    )
    
    # Supported features
    supported_currencies = models.JSONField(
        default=list,
        help_text="List of supported currency codes (e.g., ['USD', 'KES', 'EUR'])"
    )
    supports_subscriptions = models.BooleanField(default=True)
    supports_one_time = models.BooleanField(default=True)
    
    # Metadata
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Payment Provider Configuration"
        verbose_name_plural = "Payment Provider Configurations"
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.display_name} ({status})"
    
    def get_config_value(self, key, default=None):
        """Safely retrieve a config value"""
        return self.config.get(key, default)


class TenantPaymentConfig(TimeStampedModel):
    """
    Tenant-level payment provider configuration.
    Allows tenants to:
    1. Select providers for their own subscription billing
    2. Configure which providers their customers can use
    """
    tenant_id = models.CharField(max_length=50, db_index=True)
    provider = models.ForeignKey(
        PaymentProviderConfig,
        on_delete=models.CASCADE,
        related_name='tenant_configs'
    )
    
    # Usage flags
    is_enabled_for_subscription = models.BooleanField(
        default=False,
        help_text="Use this provider to pay for tenant's own subscription"
    )
    is_enabled_for_customers = models.BooleanField(
        default=False,
        help_text="Allow tenant's customers to use this provider for checkout"
    )
    
    # Optional: Tenant-specific credentials (e.g., tenant's own M-Pesa till number)
    tenant_credentials = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tenant-specific credentials (e.g., their own Stripe account, M-Pesa till)"
    )
    
    # Display settings
    priority = models.IntegerField(
        default=0,
        help_text="Display order (higher = shown first)"
    )
    custom_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom display name for this provider (optional)"
    )
    
    class Meta:
        unique_together = [('tenant_id', 'provider')]
        ordering = ['-priority', 'provider__name']
        verbose_name = "Tenant Payment Configuration"
        verbose_name_plural = "Tenant Payment Configurations"
    
    def __str__(self):
        return f"{self.tenant_id} - {self.provider.display_name}"
    
    @property
    def effective_credentials(self):
        """
        Get effective credentials (tenant-specific if available, otherwise platform)
        """
        if self.tenant_credentials:
            return self.tenant_credentials
        return self.provider.config


class PaymentMethod(TimeStampedModel):
    """
    Saved payment method for a tenant or end customer.
    Can be used for:
    - Tenant subscription billing
    - Customer checkout
    """
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_account', 'Bank Account'),
        ('wallet', 'Digital Wallet'),
    ]
    
    # Owner (either tenant or customer)
    tenant_id = models.CharField(
        max_length=50,
        db_index=True,
        null=True,
        blank=True,
        help_text="Tenant ID if this is for subscription billing"
    )
    customer_id = models.CharField(
        max_length=50,
        db_index=True,
        null=True,
        blank=True,
        help_text="Customer ID if this is for customer checkout"
    )
    
    # Provider reference
    provider = models.ForeignKey(
        PaymentProviderConfig,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    # Payment method details
    type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    display_info = models.CharField(
        max_length=100,
        help_text="Masked display info (e.g., '**** 4242', '+254 *** 1234')"
    )
    
    # Provider-specific token/ID
    provider_payment_method_id = models.CharField(
        max_length=200,
        help_text="Provider's payment method ID (e.g., Stripe pm_xxx, M-Pesa phone number)"
    )
    
    # Card-specific fields (optional)
    card_brand = models.CharField(max_length=20, blank=True)  # visa, mastercard, etc.
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
    
    def __str__(self):
        owner = self.tenant_id or self.customer_id or "Unknown"
        return f"{owner} - {self.provider.display_name} {self.display_info}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default per owner
        if self.is_default:
            # Remove default from other methods for same owner
            if self.tenant_id:
                PaymentMethod.objects.filter(
                    tenant_id=self.tenant_id,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
            elif self.customer_id:
                PaymentMethod.objects.filter(
                    customer_id=self.customer_id,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)

