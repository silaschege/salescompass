from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel
from core.models import User

# Legacy choices - kept for backward compatibility during migration
CAMPAIGN_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('scheduled', 'Scheduled'),
    ('sending', 'Sending'),
    ('sent', 'Sent'),
    ('paused', 'Paused'),
    ('cancelled', 'Cancelled'),
]

EMAIL_PROVIDER_CHOICES = [
    ('ses', 'Amazon SES'),
    ('sendgrid', 'SendGrid'),
    ('mailgun', 'Mailgun'),
    ('native', 'Django Email'),
]

BLOCK_TYPES = [
    ('hero', 'Hero Section'),
    ('features', 'Features'),
    ('testimonials', 'Testimonials'),
    ('pricing', 'Pricing'),
    ('cta', 'Call to Action'),
    ('faq', 'FAQ'),
    ('text', 'Text Content'),
    ('image', 'Image'),
    ('video', 'Video'),
    ('form', 'Contact Form'),
]

EMAIL_CATEGORY_CHOICES = [
    ('newsletter', 'Newsletter'),
    ('transactional', 'Transactional'),
    ('follow_up', 'Follow-up'),
    ('welcome', 'Welcome'),
    ('reminder', 'Reminder'),
    ('promotional', 'Promotional'),
    ('other', 'Other'),
]

MESSAGE_TYPE_CHOICES = [
    ('sms', 'SMS'),
    ('in_app', 'In-App Message'),
    ('push', 'Push Notification'),
    ('slack', 'Slack Message'),
]

MESSAGE_CATEGORY_CHOICES = [
    ('reminder', 'Reminder'),
    ('notification', 'Notification'),
    ('alert', 'Alert'),
    ('update', 'Update'),
    ('other', 'Other'),
]

VARIANT_CHOICES = [
    ('A', 'Variant A'),
    ('B', 'Variant B'),
]


class CampaignStatus(TenantModel):
    """
    Dynamic campaign status values - allows tenant-specific status tracking.
    """
    status_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'draft', 'scheduled'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Draft', 'Scheduled'
    order = models.IntegerField(default=0)
    status_is_active = models.BooleanField(default=True, help_text="Whether this status is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'status_name']
        unique_together = [('tenant', 'status_name')]
        verbose_name_plural = 'Campaign Statuses'
    
    def __str__(self):
        return self.label


class EmailProvider(TenantModel):
    """
    Dynamic email provider values - allows tenant-specific provider tracking.
    """
    provider_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'gmail', 'outlook'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Gmail', 'Outlook/Office 365'
    order = models.IntegerField(default=0)
    provider_is_active = models.BooleanField(default=True, help_text="Whether this provider is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'provider_name']
        unique_together = [('tenant', 'provider_name')]
        verbose_name_plural = 'Email Providers'
    
    def __str__(self):
        return self.label


class BlockType(TenantModel):
    """
    Dynamic block type values - allows tenant-specific block type tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'hero', 'features'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Hero Section', 'Features'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Block Types'
    
    def __str__(self):
        return self.label


class EmailCategory(TenantModel):
    """
    Dynamic email category values - allows tenant-specific category tracking.
    """
    category_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'newsletter', 'transactional'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Newsletter', 'Transactional'
    order = models.IntegerField(default=0)
    category_is_active = models.BooleanField(default=True, help_text="Whether this category is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'category_name']
        unique_together = [('tenant', 'category_name')]
        verbose_name_plural = 'Email Categories'
    
    def __str__(self):
        return self.label


class MessageType(TenantModel):
    """
    Dynamic message type values - allows tenant-specific message type tracking.
    """
    type_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'sms', 'in_app'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'SMS', 'In-App Message'
    order = models.IntegerField(default=0)
    type_is_active = models.BooleanField(default=True, help_text="Whether this type is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'type_name']
        unique_together = [('tenant', 'type_name')]
        verbose_name_plural = 'Message Types'
    
    def __str__(self):
        return self.label


class MessageCategory(TenantModel):
    """
    Dynamic message category values - allows tenant-specific category tracking.
    """
    category_name = models.CharField(max_length=20, db_index=True, help_text="e.g., 'reminder', 'notification'")  # Renamed from 'name' to avoid conflict
    label = models.CharField(max_length=50)  # e.g., 'Reminder', 'Notification'
    order = models.IntegerField(default=0)
    category_is_active = models.BooleanField(default=True, help_text="Whether this category is active")  # Renamed from 'is_active' to avoid conflict
    is_system = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order', 'category_name']
        unique_together = [('tenant', 'category_name')]
        verbose_name_plural = 'Message Categories'
    
    def __str__(self):
        return self.label


class Campaign(TenantModel):
    campaign_name = models.CharField(max_length=255, help_text="Name of the campaign")  # Renamed from 'name' to avoid conflict
    campaign_description = models.TextField(blank=True, help_text="Description of the campaign")  # Renamed from 'description' to avoid conflict
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='draft')
    # New dynamic field
    status_ref = models.ForeignKey(
        CampaignStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text="Dynamic status (replaces status field)"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    target_audience_size = models.IntegerField(default=0)
    actual_reach = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_campaigns')
    campaign_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    campaign_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    campaign_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def calculate_total_marketing_spend(self, start_date=None, end_date=None, tenant_id=None):
        """
        Calculate total marketing spend for a period.
        Includes both budget and actual costs from campaigns.
        """
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import datetime
        
        queryset = Campaign.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        else:
            # Use the current campaign's tenant if no tenant_id provided
            queryset = queryset.filter(tenant_id=self.tenant_id)
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        # Calculate total actual costs
        total_spend = queryset.aggregate(
            total_actual_cost=Sum('actual_cost'),
            total_budget=Sum('budget')
        )
        
        # Return the sum of actual costs (or budget if actual cost is not available)
        actual_cost = total_spend['total_actual_cost'] or 0
        budget_cost = total_spend['total_budget'] or 0
        
        # Use actual cost if available, otherwise use budget
        return actual_cost if actual_cost > 0 else budget_cost

    def calculate_cac_comprehensive(self, start_date=None, end_date=None, tenant_id=None):
        """
        Calculate CAC: Total Marketing Spend ÷ Number of New Customers Acquired
        """
        from core.leads.models import Lead
        from core.accounts.models import Account  # Assuming this is where customers are stored
        
        # Calculate total marketing spend
        total_spend = self.calculate_total_marketing_spend(start_date, end_date, tenant_id)
        
        # Count new customers acquired in the period
        # We'll use converted leads as a proxy for new customers
        converted_leads_query = Lead.objects.filter(status='converted')
        
        if tenant_id:
            converted_leads_query = converted_leads_query.filter(tenant_id=tenant_id)
        else:
            converted_leads_query = converted_leads_query.filter(tenant_id=self.tenant_id)
        
        if start_date:
            converted_leads_query = converted_leads_query.filter(
                lead_acquisition_date__date__gte=start_date
            )
        
        if end_date:
            converted_leads_query = converted_leads_query.filter(
                lead_acquisition_date__date__lte=end_date
            )
        
        new_customers_count = converted_leads_query.count()
        
        if new_customers_count == 0:
            return float('inf') if total_spend > 0 else 0  # Avoid division by zero
        
        cac = total_spend / new_customers_count
        return cac

    def calculate_conversion_rate(self, start_date=None, end_date=None, tenant_id=None):
        """
        Track conversion from lead to customer
        """
        from core.leads.models import Lead
        
        # Count total leads in the period
        total_leads_query = Lead.objects.all()
        
        if tenant_id:
            total_leads_query = total_leads_query.filter(tenant_id=tenant_id)
        else:
            total_leads_query = total_leads_query.filter(tenant_id=self.tenant_id)
        
        if start_date:
            total_leads_query = total_leads_query.filter(
                lead_acquisition_date__date__gte=start_date
            )
        
        if end_date:
            total_leads_query = total_leads_query.filter(
                lead_acquisition_date__date__lte=end_date
            )
        
        total_leads = total_leads_query.count()
        
        # Count converted leads in the period
        converted_leads_query = Lead.objects.filter(status='converted')
        
        if tenant_id:
            converted_leads_query = converted_leads_query.filter(tenant_id=tenant_id)
        else:
            converted_leads_query = converted_leads_query.filter(tenant_id=self.tenant_id)
        
        if start_date:
            converted_leads_query = converted_leads_query.filter(
                lead_acquisition_date__date__gte=start_date
            )
        
        if end_date:
            converted_leads_query = converted_leads_query.filter(
                lead_acquisition_date__date__lte=end_date
            )
        
        converted_leads = converted_leads_query.count()
        
        if total_leads == 0:
            return 0  # Avoid division by zero
        
        conversion_rate = (converted_leads / total_leads) * 100
        return conversion_rate

    def get_cac_by_channel(self, start_date=None, end_date=None, tenant_id=None):
        """
        Get CAC broken down by marketing channel
        """
        from core.leads.models import Lead, MarketingChannel
        from django.db.models import Sum, Count
        
        # Get all marketing channels for this tenant
        channels = MarketingChannel.objects.all()
        if tenant_id:
            channels = channels.filter(tenant_id=tenant_id)
        else:
            channels = channels.filter(tenant_id=self.tenant_id)
        
        cac_by_channel = {}
        
        for channel in channels:
            # Calculate marketing spend for this channel
            leads_for_channel = Lead.objects.filter(marketing_channel_ref=channel)
            
            if tenant_id:
                leads_for_channel = leads_for_channel.filter(tenant_id=tenant_id)
            else:
                leads_for_channel = leads_for_channel.filter(tenant_id=self.tenant_id)
            
            if start_date:
                leads_for_channel = leads_for_channel.filter(
                    lead_acquisition_date__date__gte=start_date
                )
            
            if end_date:
                leads_for_channel = leads_for_channel.filter(
                    lead_acquisition_date__date__lte=end_date
                )
            
            # Calculate spend based on cac_cost field in leads
            total_spend = leads_for_channel.aggregate(
                total_spend=Sum('cac_cost')
            )['total_spend'] or 0
            
            # Count converted leads for this channel
            converted_leads_count = leads_for_channel.filter(
                status='converted'
            ).count()
            
            if converted_leads_count == 0:
                cac = float('inf') if total_spend > 0 else 0
            else:
                cac = total_spend / converted_leads_count
            
            cac_by_channel[channel.label] = {
                'cac': cac,
                'total_spend': total_spend,
                'converted_leads': converted_leads_count,
                'total_leads': leads_for_channel.count()
            }
        
        return cac_by_channel

    def get_cac_trend(self, months=12, tenant_id=None):
        """
        Track CAC trends over time
        """
        from django.utils import timezone
        from datetime import datetime, timedelta
        from core.leads.models import Lead
        from django.db.models import Sum
        import calendar
        
        cac_trends = []
        today = timezone.now().date()
        
        for i in range(months):
            # Calculate date range for this month
            end_date = today - timedelta(days=i*30)
            start_date = end_date - timedelta(days=30)
            
            # Calculate CAC for this month
            total_spend = self.calculate_total_marketing_spend(start_date, end_date, tenant_id)
            
            # Count new customers for this month
            converted_leads_query = Lead.objects.filter(
                status='converted',
                lead_acquisition_date__date__gte=start_date,
                lead_acquisition_date__date__lte=end_date
            )
            
            if tenant_id:
                converted_leads_query = converted_leads_query.filter(tenant_id=tenant_id)
            else:
                converted_leads_query = converted_leads_query.filter(tenant_id=self.tenant_id)
            
            new_customers_count = converted_leads_query.count()
            
            cac = 0
            if new_customers_count > 0:
                cac = total_spend / new_customers_count
            
            cac_trends.append({
                'month': start_date.strftime('%Y-%m'),
                'cac': cac,
                'total_spend': total_spend,
                'new_customers': new_customers_count,
                'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            })
        
        # Reverse to show most recent first
        return list(reversed(cac_trends))

    def __str__(self):
        return self.campaign_name


class EmailTemplate(TenantModel):
    template_name = models.CharField(max_length=255, help_text="Name of the email template")  # Renamed from 'name' to avoid conflict
    subject = models.CharField(max_length=255)
    content = models.TextField(help_text="HTML content of the email")
    preview_text = models.TextField(blank=True, help_text="Preview text that appears in email clients")
    category = models.CharField(max_length=20, choices=EMAIL_CATEGORY_CHOICES, default='other')
    # New dynamic field
    category_ref = models.ForeignKey(
        EmailCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='email_templates',
        help_text="Dynamic category (replaces category field)"
    )
    template_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_templates_created')
    template_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    template_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.template_name


class LandingPage(TenantModel):
    page_name = models.CharField(max_length=255, help_text="Name of the landing page")  # Renamed from 'name' to avoid conflict
    page_slug = models.SlugField(unique=True, help_text="URL slug for the landing page")  # Renamed from 'slug' to avoid conflict with base class
    title = models.CharField(max_length=255, help_text="Page title for SEO")
    meta_description = models.TextField(blank=True, help_text="Meta description for SEO")
    page_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='landing_pages_created')
    page_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    page_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.page_name


class LandingPageBlock(TenantModel):
    landing_page = models.ForeignKey(LandingPage, on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPES)
    # New dynamic field
    block_type_ref = models.ForeignKey(
        BlockType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='landing_page_blocks',
        help_text="Dynamic block type (replaces block_type field)"
    )
    content = models.JSONField(default=dict, blank=True)  # Block-specific content
    order = models.IntegerField(default=0, help_text="Order of the block on the page")
    block_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    block_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    block_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.block_type} block on {self.landing_page.name}"


class MessageTemplate(TenantModel):
    template_name = models.CharField(max_length=255, help_text="Name of the message template")  # Renamed from 'name' to avoid conflict
    message_template_description = models.TextField(blank=True)
    content = models.TextField(help_text="Message content with merge tag support")
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    # New dynamic field
    message_type_ref = models.ForeignKey(
        MessageType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='message_templates',
        help_text="Dynamic message type (replaces message_type field)"
    )
    category = models.CharField(max_length=20, choices=MESSAGE_CATEGORY_CHOICES, default='other')
    # New dynamic field
    category_ref = models.ForeignKey(
        MessageCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='message_templates',
        help_text="Dynamic category (replaces category field)"
    )
    template_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='message_templates_created')
    template_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    template_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.template_name


class EmailCampaign(TenantModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_campaigns')
    campaign_name = models.CharField(max_length=255, help_text="Name of the email campaign")  # Renamed from 'name' to avoid conflict
    subject = models.CharField(max_length=255)
    content = models.TextField()
    recipients = models.JSONField(default=list, help_text="List of recipient emails or criteria")
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    scheduled_send_time = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    email_provider = models.CharField(max_length=20, choices=EMAIL_PROVIDER_CHOICES, default='native')
    # New dynamic field
    email_provider_ref = models.ForeignKey(
        EmailProvider,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='email_campaigns',
        help_text="Dynamic email provider (replaces email_provider field)"
    )
    tracking_enabled = models.BooleanField(default=True)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    bounce_count = models.IntegerField(default=0)
    complaint_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_campaigns_created')
    campaign_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    campaign_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.campaign_name


class CampaignRecipient(TenantModel):
    email_campaign = models.ForeignKey(
        EmailCampaign, 
        on_delete=models.CASCADE, 
        related_name='recipient_list'
    )
    email = models.EmailField()
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    merge_data = models.JSONField(default=dict, blank=True, help_text="Data for personalization")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('unsubscribed', 'Unsubscribed'),
    ], default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    recipient_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class

    def __str__(self):
        return f"{self.email} - {self.email_campaign.name}"


class ABAutomatedTest(TenantModel):
    test_name = models.CharField(max_length=255, help_text="Name of the A/B test")  # Renamed from 'name' to avoid conflict
    test_description = models.TextField(blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ab_tests')
    variant_a = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='ab_tests_as_variant_a')
    variant_b = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='ab_tests_as_variant_b')
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sample_size = models.IntegerField(default=100)
    winner = models.CharField(max_length=1, choices=VARIANT_CHOICES, blank=True, null=True)
    winning_metric = models.CharField(max_length=50, blank=True, help_text="Metric that determined the winner")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ab_tests_created')
    test_created_at = models.DateTimeField(auto_now_add=True)  # Renamed from 'created_at' to avoid conflict with base class
    test_updated_at = models.DateTimeField(auto_now=True)  # Renamed from 'updated_at' to avoid conflict with base class

    def __str__(self):
        return self.test_name
