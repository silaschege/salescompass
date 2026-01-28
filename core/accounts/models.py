from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from core.models import User, TimeStampedModel
from tenants.models import TenantAwareModel as TenantModel



 




# Role model has been moved to access_control.role_models
# Import for backward compatibility
from access_control.role_models import Role


class UserActivityLog(models.Model):
    """Model for tracking user-specific activities and sessions"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100, choices=[
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('session_start', 'Session Start'),
        ('session_end', 'Session End'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('mfa_setup', 'MFA Setup'),
        ('mfa_disable', 'MFA Disable'),
        ('permission_change', 'Permission Change'),
        ('role_change', 'Role Change'),
        ('data_access', 'Data Access'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('record_create', 'Record Create'),
        ('record_update', 'Record Update'),
        ('record_delete', 'Record Delete'),
        ('file_upload', 'File Upload'),
        ('file_download', 'File Download'),
        ('api_call', 'API Call'),
        ('settings_change', 'Settings Change'),
        ('configuration_change', 'Configuration Change'),
    ])
    resource_type = models.CharField(max_length=100, blank=True, help_text="Type of resource accessed")
    resource_id = models.CharField(max_length=100, blank=True, help_text="ID of the resource accessed")
    details = models.JSONField(default=dict, blank=True, help_text="Additional action details")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="User agent string")
    session_id = models.CharField(max_length=100, blank=True, help_text="Session identifier")
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)
    duration_seconds = models.FloatField(null=True, blank=True, help_text="Duration of the action in seconds")
    
    class Meta:
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"


class UserOnboardingWorkflow(models.Model):
    """Model for managing user onboarding processes"""
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_workflow')
    status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ], default='not_started')
    steps_completed = models.JSONField(default=list, blank=True, help_text="List of completed onboarding steps")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion_days = models.IntegerField(default=7, help_text="Estimated days to complete onboarding")
    
    # Step completion flags
    profile_setup_complete = models.BooleanField(default=False)
    security_setup_complete = models.BooleanField(default=False)
    tutorial_complete = models.BooleanField(default=False)
    integration_setup_complete = models.BooleanField(default=False)
    team_invitation_sent = models.BooleanField(default=False)
    team_invitation_accepted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "User Onboarding Workflow"
        verbose_name_plural = "User Onboarding Workflows"
    
    def __str__(self):
        return f"Onboarding for {self.user.email} - {self.status}"


class UserCertification(models.Model):
    """Model for tracking user access certifications and reviews"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    certifier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certifications_performed')
    certification_type = models.CharField(max_length=50, choices=[
        ('access_review', 'Access Review'),
        ('role_verification', 'Role Verification'),
        ('permission_audit', 'Permission Audit'),
        ('compliance_check', 'Compliance Check'),
    ])
    reason = models.TextField(blank=True, help_text="Reason for certification")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revoked', 'Revoked'),
    ], default='pending')
    next_review_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "User Certification"
        verbose_name_plural = "User Certifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.certification_type} for {self.user.email} - {self.status}"


class MFADevice(models.Model):
    """Model for managing MFA devices per user"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_devices')
    device_type = models.CharField(max_length=20, choices=[
        ('totp', 'Time-based OTP'),
        ('hotp', 'HMAC-based OTP'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('hardware', 'Hardware Token'),
        ('push_notification', 'Push Notification'),
    ])
    device_name = models.CharField(max_length=100, help_text="Friendly name for the device")
    secret_key = models.CharField(max_length=32, help_text="Secret key for TOTP/HOTP")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary MFA device?")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    backup_codes = models.JSONField(default=list, blank=True, help_text="List of backup codes")
    backup_codes_generated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "MFA Device"
        verbose_name_plural = "MFA Devices"
        unique_together = ['user', 'device_name']
    
    def __str__(self):
        return f"{self.device_type} for {self.user.email} - {self.device_name}"


class UserAccessReview(models.Model):
    """Model for formalizing access review processes"""
    id = models.AutoField(primary_key=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='access_reviews_conducted')
    subject_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_reviews_received')
    review_cycle = models.CharField(max_length=50, choices=[
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('annually', 'Annually'),
        ('on_demand', 'On Demand'),
    ])
    review_type = models.CharField(max_length=50, choices=[
        ('role_based', 'Role Based'),
        ('permission_based', 'Permission Based'),
        ('data_access', 'Data Access'),
        ('system_access', 'System Access'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ], default='pending')
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)
    access_confirmed = models.BooleanField(null=True, blank=True, help_text="Whether access was confirmed or revoked")
    access_revoked_reason = models.TextField(blank=True, help_text="Reason if access was revoked")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Access Review"
        verbose_name_plural = "User Access Reviews"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Access review for {self.subject_user.email} by {self.reviewer.email if self.reviewer else 'System'}"


class RolePermissionAudit(models.Model):
    """Model for tracking role and permission changes"""
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permission_audits')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='role_permission_audits')
    action = models.CharField(max_length=20, choices=[
        ('permission_added', 'Permission Added'),
        ('permission_removed', 'Permission Removed'),
        ('role_assigned', 'Role Assigned'),
        ('role_unassigned', 'Role Unassigned'),
        ('role_created', 'Role Created'),
        ('role_updated', 'Role Updated'),
        ('role_deleted', 'Role Deleted'),
    ])
    permission = models.ForeignKey('auth.Permission', on_delete=models.SET_NULL, null=True, blank=True)
    old_value = models.TextField(blank=True, help_text="Previous value before change")
    new_value = models.TextField(blank=True, help_text="New value after change")
    reason = models.TextField(blank=True, help_text="Reason for the change")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Role Permission Audit"
        verbose_name_plural = "Role Permission Audits"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} for {self.role.name} - {self.timestamp}"



class Account(TenantModel, TimeStampedModel):
    """
    CRM Account model representing a business entity (Company).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('at_risk', 'At Risk'),
        ('churned', 'Churned'),
    ]

    INDUSTRY_CHOICES = [
        ('tech', 'Technology'),
        ('manufacturing', 'Manufacturing'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('retail', 'Retail'),
        ('energy', 'Energy'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]

    TIER_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    ESG_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    account_name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, choices=INDUSTRY_CHOICES, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    
    # Pricing
    price_list = models.ForeignKey('products.PriceList', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='accounts', help_text="Assigned price list for this account")
    
    # Address Fields
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)

    # Business Details
    description = models.TextField(blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Annual revenue")
    number_of_employees = models.PositiveIntegerField(null=True, blank=True)
    
    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    # Meta
    tags = models.JSONField(default=list, blank=True, help_text="List of tags")
    last_activity_at = models.DateTimeField(null=True, blank=True)

    # KPIs/Health
    health_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    esg_engagement = models.CharField(max_length=20, choices=ESG_CHOICES, default='low')

    # ESG Related Fields - Added to support template
    overall_esg_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Overall ESG score")
    csr_ready = models.BooleanField(default=False, help_text="Whether the account is ready for CSR reporting")
    tco2e_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Tonnes of CO2 equivalent saved")
    sustainability_goals = models.TextField(blank=True, help_text="Sustainability goals for the account")
    esg_certified = models.BooleanField(default=False, help_text="Whether the account has ESG certification")

    # Compliance
    gdpr_consent = models.BooleanField(default=False)
    ccpa_consent = models.BooleanField(default=False)
    
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_accounts')
    # Hierarchy
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subsidiaries', help_text="Parent account for hierarchy")
    
    # Team
    users = models.ManyToManyField(User, related_name='associated_accounts', blank=True, through='AccountTeamMember')
    
    # Market Intelligence
    partners = models.JSONField(default=list, blank=True, help_text="List of partners involved with this account")
    competitors = models.JSONField(default=list, blank=True, help_text="List of competitors for this account")
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.account_name


class AccountsUserProfile(models.Model):
    """
    Extension of the User model specifically for the Accounts applet.
    Stores user preferences and settings for the accounts module.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accounts_profile')
    favorite_accounts = models.ManyToManyField(Account, blank=True, related_name='favorited_by')
    settings = models.JSONField(default=dict, blank=True, help_text="User preferences for the accounts app UI")
    
    def __str__(self):
        return f"Accounts Profile for {self.user.email}"


class AccountTeamMember(TenantModel):
    """
    Through-model for Account users (Team Members) with roles.
    """
    ROLE_CHOICES = [
        ('account_manager', 'Account Manager'),
        ('sales_engineer', 'Sales Engineer'),
        ('executive_sponsor', 'Executive Sponsor'),
        ('customer_success', 'Customer Success Manager'),
        ('support_lead', 'Support Lead'),
        ('other', 'Member'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='other')
    is_primary = models.BooleanField(default=False, help_text="Is this the primary contact for this role?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['account', 'user']
        verbose_name = "Account Team Member"
        verbose_name_plural = "Account Team Members"

    def __str__(self):
        return f"{self.user} - {self.role} ({self.account})"


class Contact(TenantModel, TimeStampedModel):
    """
    Contact model representing an individual contact.
    """
    ESG_INFLUENCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    COMMUNICATION_PREFERENCE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('mail', 'Mail'),
        ('text', 'Text/SMS'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contacts', null=True, blank=True)
    
    # Additional fields that are referenced in templates but missing
    role = models.CharField(max_length=100, blank=True, help_text="Role or job title of the contact")
    communication_preference = models.CharField(max_length=20, choices=COMMUNICATION_PREFERENCE_CHOICES, 
                                               default='email', help_text="Preferred method of communication")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary contact for the account?")
    esg_influence = models.CharField(max_length=20, choices=ESG_INFLUENCE_CHOICES, default='low',
                                     help_text="Level of influence on ESG decisions")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# RoleAppPermission has been replaced by AccessControl in access_control app
# This class is deprecated and will be removed in a future version