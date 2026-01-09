from django.db import models
from core.models import TimeStampedModel
from tenants.models import TenantAwareModel 
from core.models import User
from django.utils import timezone
from django.db.models import JSONField


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
    ('C', 'Variant C'),
    ('D', 'Variant D'),
]


class CampaignStatus(TenantAwareModel, TimeStampedModel):
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


class EmailProvider(TenantAwareModel, TimeStampedModel):
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


class Segment(TenantAwareModel, TimeStampedModel):
    """
    Model for defining audience segments for targeted email campaigns.
    Segments can be based on various criteria like demographics, behavior, etc.
    """
    SEGMENT_TYPES = [
        ('static', 'Static'),
        ('dynamic', 'Dynamic'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    segment_type = models.CharField(max_length=20, choices=SEGMENT_TYPES, default='static')
    criteria = JSONField(default=dict, blank=True, help_text="Criteria for dynamic segments")
    member_count = models.IntegerField(default=0, help_text="Number of contacts in this segment")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    def update_member_count(self):
        """Update the member count based on current segment members"""
        self.member_count = self.segment_members.filter(is_active=True).count()
        self.save()


class SegmentMember(TenantAwareModel, TimeStampedModel):
    """
    Model for storing members (contacts) in segments.
    For static segments, members are manually added.
    For dynamic segments, members are automatically added based on criteria.
    """
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='segment_members')
    # Assuming there's a Contact model in the leads app
    contact = models.ForeignKey('leads.Lead', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_removed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['segment', 'contact']
        
    def __str__(self):
        return f"{self.contact} in {self.segment}"


class BlockType(TenantAwareModel, TimeStampedModel):
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


class EmailCategory(TenantAwareModel, TimeStampedModel):
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


class MessageType(TenantAwareModel, TimeStampedModel):
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


class MessageCategory(TenantAwareModel, TimeStampedModel):
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


class Campaign(TenantAwareModel, TimeStampedModel):
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
    # Remove the created_at and updated_at fields since they're inherited

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

    # ... rest of the methods remain the same ...

    def __str__(self):
        return self.campaign_name


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


class EmailTemplate(TenantAwareModel, TimeStampedModel):
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
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return self.template_name


class LandingPage(TenantAwareModel, TimeStampedModel):
    page_name = models.CharField(max_length=255, help_text="Name of the landing page")  # Renamed from 'name' to avoid conflict
    page_slug = models.SlugField(unique=True, help_text="URL slug for the landing page")  # Renamed from 'slug' to avoid conflict with base class
    title = models.CharField(max_length=255, help_text="Page title for SEO")
    meta_description = models.TextField(blank=True, help_text="Meta description for SEO")
    page_is_active = models.BooleanField(default=True)  # Renamed from 'is_active' to avoid conflict with base class
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='landing_pages_created')
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return self.page_name


class LandingPageBlock(TenantAwareModel, TimeStampedModel):
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
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return f"{self.block_type} block on {self.landing_page.page_name}"



class MessageTemplate(TenantAwareModel, TimeStampedModel):
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
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return self.template_name
    
class EmailCampaign(TenantAwareModel, TimeStampedModel):
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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_campaigns_created')
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return self.campaign_name
    
    def get_deliverability_stats(self):
        """
        Calculate deliverability statistics for this email campaign.
        """
        total_sent = self.email_events.filter(event_type='sent').count()
        delivered = self.email_events.filter(event_type='delivered').count()
        opened = self.email_events.filter(event_type='opened').count()
        clicked = self.email_events.filter(event_type='clicked').count()
        bounced = self.email_events.filter(event_type='bounced').count()
        spam = self.email_events.filter(event_type='spam').count()
        
        stats = {
            'total_sent': total_sent,
            'delivered': delivered,
            'opened': opened,
            'clicked': clicked,
            'bounced': bounced,
            'spam': spam,
            'delivery_rate': (delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
            'click_rate': (clicked / delivered * 100) if delivered > 0 else 0,
            'bounce_rate': (bounced / total_sent * 100) if total_sent > 0 else 0,
            'spam_rate': (spam / delivered * 100) if delivered > 0 else 0,
        }
        
        return stats



class CampaignRecipient(TenantAwareModel, TimeStampedModel):
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
    # Remove the created_at and updated_at fields since they're inherited

    def __str__(self):
        return f"{self.email} - {self.email_campaign.campaign_name}"

class ABAutomatedTest(TenantAwareModel, TimeStampedModel):
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


class EmailIntegration(TenantAwareModel, TimeStampedModel):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook/Office 365'),
    ]

    # ADD THIS FIELD TO OVERRIDE THE ONE IN TenantAwareModel:
    tenant = models.ForeignKey(
        'tenants.Tenant', # Ensure this matches your actual Tenant model path
        on_delete=models.CASCADE,
        related_name='marketing_email_integrations' # This must be unique
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketing_email_integrations_user')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    
    # New dynamic field
    provider_ref = models.ForeignKey(
        EmailProvider,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='marketing_email_integrations_ref', # Made this unique too
        help_text="Dynamic provider (replaces provider field)"
    )
    email_address = models.EmailField()
    integration_is_active = models.BooleanField(default=True, help_text="Whether this integration is active")
    last_sync = models.DateTimeField(null=True, blank=True)
    api_key = models.TextField(blank=True, help_text="API key or access token")
    refresh_token = models.TextField(blank=True, help_text="Refresh token for OAuth")

    def __str__(self):
        return f"{self.email_address} ({self.provider})"



class ABTest(TenantAwareModel, TimeStampedModel):
    """
    Model representing an A/B test for marketing campaigns.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name='ab_new_tests')
    is_active = models.BooleanField(default=False)
    auto_winner = models.BooleanField(default=False, help_text="Automatically declare winner")
    winner_variant = models.CharField(max_length=1, choices=VARIANT_CHOICES, blank=True, null=True)
    is_winner_declared = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metrics tracking fields
    start_date = models.DateTimeField(null=True, blank=True, help_text="When the test started")
    end_date = models.DateTimeField(null=True, blank=True, help_text="When the test ended")
    confidence_level = models.FloatField(default=95.0, help_text="Confidence level for statistical significance (%)")

    def __str__(self):
        return self.name

    @property
    def total_responses(self):
        # Calculate total responses across all variants
        return sum(variant.responses.count() if hasattr(variant, 'responses') else 0 for variant in self.variants.all())
    
    @property
    def duration(self):
        """Return the duration of the test in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
    
    def get_variant_stats(self):
        """Get statistics for each variant"""
        stats = []
        for variant in self.variants.all():
            total_responses = variant.responses.count()
            opens = variant.responses.filter(opened_at__isnull=False).count()
            clicks = variant.responses.filter(clicked_at__isnull=False).count()
            
            open_rate = (opens / total_responses * 100) if total_responses > 0 else 0
            click_rate = (clicks / total_responses * 100) if total_responses > 0 else 0
            ctr = (clicks / opens * 100) if opens > 0 else 0
            
            stats.append({
                'variant': variant,
                'total_responses': total_responses,
                'opens': opens,
                'clicks': clicks,
                'open_rate': open_rate,
                'click_rate': click_rate,
                'ctr': ctr,
            })
        return stats
    
    def declare_winner(self):
        """Declare the winning variant based on highest click-through rate"""
        if self.is_winner_declared:
            return
        
        stats = self.get_variant_stats()
        if not stats:
            return
            
        # Find variant with highest CTR
        winner = max(stats, key=lambda x: x['ctr'])
        self.winner_variant = winner['variant'].variant
        self.is_winner_declared = True
        self.end_date = timezone.now()
        self.save()
        
        return winner['variant']


class ABTestVariant(TenantAwareModel, TimeStampedModel):
    """
    Model representing a variant in an A/B test.
    """
    ab_test = models.ForeignKey('ABTest', on_delete=models.CASCADE, related_name='variants')
    variant = models.CharField(max_length=1, choices=VARIANT_CHOICES)
    assignment_rate = models.FloatField(default=0.5, help_text="Proportion of recipients (0.0-1.0)")
    email_template = models.ForeignKey('EmailTemplate', on_delete=models.CASCADE, null=True, blank=True)
    landing_page = models.ForeignKey('LandingPage', on_delete=models.CASCADE, null=True, blank=True)
    question_text = models.TextField(blank=True, help_text="Question for survey-based tests")
    follow_up_question = models.TextField(blank=True, help_text="Follow-up question if needed")
    delivery_delay_hours = models.IntegerField(default=0, help_text="Delay in hours before sending")
    
    # Metrics tracking fields
    sent_count = models.IntegerField(default=0, help_text="Number of emails sent")
    open_count = models.IntegerField(default=0, help_text="Number of emails opened")
    click_count = models.IntegerField(default=0, help_text="Number of links clicked")
    conversion_count = models.IntegerField(default=0, help_text="Number of conversions")
    
    def __str__(self):
        return f"Variant {self.get_variant_display()}"

    def get_variant_display(self):
        return dict(VARIANT_CHOICES).get(self.variant, self.variant)
    
    @property
    def open_rate(self):
        """Calculate open rate"""
        if self.sent_count > 0:
            return (self.open_count / self.sent_count) * 100
        return 0
    
    @property
    def click_rate(self):
        """Calculate click rate"""
        if self.sent_count > 0:
            return (self.click_count / self.sent_count) * 100
        return 0
    
    @property
    def ctr(self):
        """Calculate click-through rate (clicks per open)"""
        if self.open_count > 0:
            return (self.click_count / self.open_count) * 100
        return 0
    
    @property
    def conversion_rate(self):
        """Calculate conversion rate"""
        if self.sent_count > 0:
            return (self.conversion_count / self.sent_count) * 100
        return 0


class ABTestResponse(TenantAwareModel, TimeStampedModel):
    """
    Model representing a response to an A/B test variant.
    """
    ab_test_variant = models.ForeignKey(ABTestVariant, on_delete=models.CASCADE, related_name='responses')
    email = models.EmailField()
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Additional tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    conversion_at = models.DateTimeField(null=True, blank=True, help_text="When a conversion event occurred")
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Value of conversion")
    
    def __str__(self):
        return f"Response to {self.ab_test_variant} from {self.email}"
    
    @property
    def is_opened(self):
        return self.opened_at is not None
    
    @property
    def is_clicked(self):
        return self.clicked_at is not None
    
    @property
    def is_converted(self):
        return self.conversion_at is not None


class NurtureCampaign(TenantAwareModel, TimeStampedModel):
    """
    Model for automated nurture campaigns that send a sequence of emails
    to leads over time based on their behavior and stage in the funnel.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    target_segment = models.ForeignKey(Segment, on_delete=models.CASCADE, related_name='nurture_campaigns')
    trigger_event = models.CharField(
        max_length=100, 
        help_text="Event that starts the nurture (e.g., form submission, page visit)"
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class NurtureStep(TenantAwareModel, TimeStampedModel):
    """
    Individual steps in a nurture campaign sequence.
    Each step defines an email to be sent after a certain delay.
    """
    nurture_campaign = models.ForeignKey(NurtureCampaign, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField(help_text="Order of the step in the sequence")
    email_template = models.ForeignKey('EmailTemplate', on_delete=models.CASCADE)
    delay_days = models.PositiveIntegerField(
        default=0, 
        help_text="Days to wait after trigger or previous step before sending"
    )
    delay_hours = models.PositiveIntegerField(
        default=0, 
        help_text="Additional hours to wait (added to delay_days)"
    )
    
    class Meta:
        ordering = ['step_number']
        unique_together = ['nurture_campaign', 'step_number']
        
    def __str__(self):
        return f"Step {self.step_number} of {self.nurture_campaign.name}"


class NurtureCampaignEnrollment(TenantAwareModel, TimeStampedModel):
    """
    Tracks which leads are enrolled in which nurture campaigns.
    """
    enrollment_status_choices = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
    ]
    
    nurture_campaign = models.ForeignKey(NurtureCampaign, on_delete=models.CASCADE)
    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=enrollment_status_choices, default='active')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    current_step = models.ForeignKey(NurtureStep, on_delete=models.SET_NULL, null=True, blank=True)
    last_activity_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['nurture_campaign', 'lead']
        
    def __str__(self):
        return f"{self.lead} in {self.nurture_campaign}"


class DripCampaign(TenantAwareModel, TimeStampedModel):
    """
    Model for broad, scheduled drip campaigns (e.g., welcoming new users).
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class DripStep(TenantAwareModel, TimeStampedModel):
    """
    Individual steps in a drip campaign sequence.
    """
    STEP_TYPES = [
        ('email', 'Send Email'),
        ('wait', 'Wait'),
    ]
    
    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(max_length=20, choices=STEP_TYPES, default='email')
    email_template = models.ForeignKey('EmailTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    wait_days = models.PositiveIntegerField(default=0)
    wait_hours = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"Step {self.order}: {self.get_step_type_display()} in {self.drip_campaign.name}"


class DripEnrollment(TenantAwareModel, TimeStampedModel):
    """
    Tracks which accounts/leads are enrolled in which drip campaigns.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    drip_campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='enrollments')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, null=True, blank=True)
    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_step = models.ForeignKey(DripStep, on_delete=models.SET_NULL, null=True, blank=True)
    next_execution_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['drip_campaign', 'email']
        
    def __str__(self):
        return f"{self.email} in {self.drip_campaign}"


class EmailEvent(TenantAwareModel, TimeStampedModel):
    """
    Model for tracking email events for deliverability monitoring.
    """
    EVENT_TYPES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('spam', 'Marked as Spam'),
        ('unsubscribed', 'Unsubscribed'),
    ]
    
    email_campaign = models.ForeignKey('EmailCampaign', on_delete=models.CASCADE, related_name='email_events')
    recipient = models.ForeignKey('CampaignRecipient', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    details = JSONField(default=dict, blank=True, help_text="Additional details about the event")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.event_type} for {self.recipient.email}"

