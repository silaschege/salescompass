from django.db import models
from django.utils import timezone


class FeatureFlag(models.Model):
    """Feature flag for release management"""
    
    # Flag Details
    key = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=False)
    
    # Rollout
    rollout_percentage = models.IntegerField(default=0, help_text="0-100: Percentage of users to enable")
    
    # Audit
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        status = "ON" if self.is_active else "OFF"
        return f"{self.name} ({self.key}) - {status} - {self.rollout_percentage}%"
    
    def is_enabled_for_user(self, user):
        """Check if feature is enabled for a specific user"""
        if not self.is_active:
            return False
        
        # Check targeting rules
        targets = self.targets.filter(is_active=True)
        
        # Check if user matches any target
        for target in targets:
            if target.matches_user(user):
                return True
        
        # Fallback to percentage rollout
        if self.rollout_percentage == 100:
            return True
        elif self.rollout_percentage == 0:
            return False
        else:
            # Use user ID for consistent hashing
            user_hash = hash(f"{self.key}:{user.id}") % 100
            return user_hash < self.rollout_percentage


class FeatureTarget(models.Model):
    """Targeting rules for feature flags"""
    
    TARGET_TYPE_CHOICES = [
        ('user_id', 'Specific User ID'),
        ('tenant_id', 'Specific Tenant ID'),
        ('role', 'User Role'),
        ('plan', 'Subscription Plan'),
        ('cohort', 'User Cohort'),
    ]
    
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='targets')
    
    target_type = models.CharField(max_length=50, choices=TARGET_TYPE_CHOICES)
    target_value = models.CharField(max_length=200, help_text="e.g., 'admin', 'premium', '123'")
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['feature_flag', 'target_type']
        unique_together = ['feature_flag', 'target_type', 'target_value']
    
    def __str__(self):
        return f"{self.feature_flag.key} -> {self.target_type}:{self.target_value}"
    
    def matches_user(self, user):
        """Check if this target matches the given user"""
        if self.target_type == 'user_id':
            return str(user.id) == self.target_value
        elif self.target_type == 'tenant_id':
            return str(getattr(user, 'tenant_id', None)) == self.target_value
        elif self.target_type == 'role':
            return hasattr(user, 'role') and user.role and user.role.name.lower() == self.target_value.lower()
        elif self.target_type == 'plan':
            # Would need to check user's tenant's plan
            return False  # Implement based on your tenant/plan structure
        elif self.target_type == 'cohort':
            # Implement cohort logic
            return False
        return False
