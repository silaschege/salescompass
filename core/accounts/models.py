from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from core.models import User
from tenants.models import TenantAwareModel as TenantModel




class TeamRole(TenantModel):
    """
    Dynamic team role values - allows tenant-specific team role tracking.
    """
    role_name = models.CharField(max_length=50, db_index=True, help_text="e.g., 'sales_rep', 'sales_manager'")
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    role_is_active = models.BooleanField(default=True, help_text="Whether this role is active")
    is_system = models.BooleanField(default=False)
    # Override tenant to avoid clash with settings_app.TeamRole
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='account_team_roles')
    
    class Meta:
        ordering = ['order', 'role_name']
        unique_together = [('tenant', 'role_name')]
        verbose_name_plural = 'Team Roles'
    
    def __str__(self):
        return self.label


class Territory(TenantModel):
    """
    Dynamic territory values - allows tenant-specific territory tracking.
    """
    territory_name = models.CharField(max_length=100, db_index=True, help_text="e.g., 'north_america', 'emea'")
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    territory_is_active = models.BooleanField(default=True, help_text="Whether this territory is active")
    is_system = models.BooleanField(default=False)
    # Override tenant to avoid clash with settings_app.Territory
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='account_territories')
    
    class Meta:
        ordering = ['order', 'territory_name']
        unique_together = [('tenant', 'territory_name')]
        verbose_name_plural = 'Territories'
    
    def __str__(self):
        return self.label
class OrganizationMember(TenantModel):
    """
    Represents a person in a specific tenant organization.
    This replaces the TeamMember model from settings_app.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization_membership')
    
    # Role using dynamic reference
    role = models.CharField(max_length=50, choices=[
        ('sales_rep', 'Sales Representative'),
        ('sales_manager', 'Sales Manager'),
        ('account_manager', 'Account Manager'),
        ('sales_director', 'Sales Director'),
        ('ceo', 'CEO'),
        ('admin', 'Administrator'),
    ])
    
    # New dynamic field for role
    role_ref = models.ForeignKey(
        TeamRole,  # Reference to the dynamic model
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='organization_members',
        help_text="Dynamic role (replaces role field)"
    )
    
    # Territory using dynamic reference
    territory = models.CharField(max_length=100, choices=[
        ('north_america', 'North America'),
        ('emea', 'EMEA'),
        ('apac', 'APAC'),
        ('latam', 'Latin America'),
    ], blank=True)
    
    # New dynamic field for territory
    territory_ref = models.ForeignKey(
        Territory,  # Reference to the dynamic model
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='organization_members',
        help_text="Dynamic territory (replaces territory field)"
    )
    
    # Manager relationship
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    
    # Status using dynamic reference
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('onboarding', 'Onboarding'),
        ('leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ], default='onboarding')
    
    # New dynamic field for status
    status_ref = models.ForeignKey(
        'self',  # Self reference for status
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_members_by_status',
        help_text="Dynamic status (replaces status field)"
    )
    
    # Employment dates
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Quota information
    quota_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    quota_period = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], default='quarterly')
    
    # New dynamic field for quota period
    quota_period_ref = models.ForeignKey(
        'self',  # Self reference for period
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_members_by_period',
        help_text="Dynamic quota period (replaces quota_period field)"
    )
    
    # Commission information
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, 
                                        help_text="Commission rate (e.g. 10.0 for 10%)")
    
    # Territory Performance Metrics
    territory_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                     help_text="Performance score within assigned territory (0-100)")
    territory_quota_attainment = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                    help_text="Percentage of territory quota attained")
    territory_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                                   help_text="Lead to opportunity conversion rate in territory (%)")
    territory_revenue_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                                        help_text="Revenue contribution to assigned territory")

    def __str__(self):
        return f"{self.user.email} - {self.role}"
    
    class Meta:
        verbose_name = "Organization Member"
        verbose_name_plural = "Organization Members"

class Role(models.Model):
    """Model for managing user roles and permissions"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('auth.Permission', blank=True)
    is_system_role = models.BooleanField(default=False)
    is_assignable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['name']
    
    def __str__(self):
        return self.name


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


class Account(TenantModel):
    """
    CRM Account model representing a business entity (Company).
    """
    account_name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_accounts')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.account_name


class Contact(TenantModel):
    """
    Contact model representing an individual contact.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contacts', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class RoleAppPermission(models.Model):
    """
    Model definition for RoleAppPermission
    Controls which apps are visible to which roles.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='app_permissions')
    app_identifier = models.CharField(max_length=100, help_text="Unique identifier for the app (e.g., 'reachout', 'tenants')")
    is_visible = models.BooleanField(default=True, help_text="Whether this app is visible to the role")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['role', 'app_identifier']
        verbose_name = 'Role App Permission'
        verbose_name_plural = 'Role App Permissions'

    def __str__(self):
        return f"{self.role.name} - {self.app_identifier}: {'Visible' if self.is_visible else 'Hidden'}"