from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from core.models import User
from tenants.models import TenantAwareModel as TenantModel


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