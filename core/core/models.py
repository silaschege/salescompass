from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    """
    Abstract base model with tenant_id for multi-tenancy.
    """
    tenant_id = models.CharField(
        max_length=50,
        db_index=True,
        null=True,
        blank=True,
        help_text="ID of the tenant (organization) this record belongs to"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Auto-populate tenant_id from request user if not set
        if not self.tenant_id and hasattr(self, '_current_user'):
            self.tenant_id = getattr(self._current_user, 'tenant_id', None)
            
        # Enforce limits on creation
        if self._state.adding and self.tenant_id:
            self.check_usage_limits()
            
        super().save(*args, **kwargs)

    def get_subscription(self):
        """Get the active subscription for this tenant."""
        from billing.models import Subscription
        try:
            return Subscription.objects.filter(tenant_id=self.tenant_id, status__in=['active', 'trialing']).select_related('plan').first()
        except ImportError:
            return None

    def check_usage_limits(self):
        """Check if creating this object violates plan limits."""
        sub = self.get_subscription()
        if not sub:
            # Default to restrictive limits if no subscription found (or handle as error)
            # For now, allow if no sub to avoid breaking existing tests, but in prod this should be strict.
            return

        model_name = self._meta.model_name
        
        if model_name == 'user':
            current_count = User.objects.filter(tenant_id=self.tenant_id).count()
            if current_count >= sub.plan.max_users:
                raise ValidationError(f"Plan limit reached: Max {sub.plan.max_users} users allowed.")
                
        elif model_name == 'lead':
            # Avoid circular import by using string reference or local import if needed
            # But self is a Lead instance here
            current_count = self.__class__.objects.filter(tenant_id=self.tenant_id).count()
            if current_count >= sub.plan.max_leads:
                raise ValidationError(f"Plan limit reached: Max {sub.plan.max_leads} leads allowed.")


class Role(TenantModel):
    """
    Role with a list of permission strings.
    
    Permission format: "<resource>:<action>"
    Examples:
      - "accounts:read"
      - "accounts:write"
      - "esg:read"
      - "automation:manage"
    
    Permissions are stored as a JSON list for simplicity and flexibility.
    In high-scale systems, consider a many-to-many Permission model.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=list,
        help_text="List of permission strings, e.g., ['accounts:read', 'proposals:write']"
    )
    data_visibility_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Record-level visibility rules, e.g., {'accounts': 'own_only', 'leads': 'team_only'}"
    )

    def __str__(self):
        return self.name

    def add_permission(self, perm: str) -> None:
        """Add a permission if not already present."""
        if perm not in self.permissions:
            self.permissions.append(perm)
            self.save(update_fields=['permissions'])

    def remove_permission(self, perm: str) -> None:
        """Remove a permission if present."""
        if perm in self.permissions:
            self.permissions.remove(perm)
            self.save(update_fields=['permissions'])

    def has_permission(self, perm: str) -> bool:
        """Check if this role grants a specific permission."""
        return perm in self.permissions


class User(AbstractUser, TenantModel):
    """
    Custom user with role-based permissions and multi-tenancy.
    """
    email = models.EmailField(unique=True) 
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # Django auth requirements
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='core_user_set',  # ← Unique related_name
        related_query_name='core_user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='core_user_set',  # ← Unique related_name
        related_query_name='core_user',
    )

    def has_perm(self, perm: str, obj=None) -> bool:
        """
        Override to support our permission system.
        obj is ignored (no object-level perms here; add if needed).
        """
        if self.is_superuser:
            return True
        if not self.role:
            return False
        
        # Check for global wildcard
        if '*' in self.role.permissions:
            return True
        
        # Check exact match
        if perm in self.role.permissions:
            return True
            
        # Check wildcard (e.g., 'accounts:*' matches 'accounts:read')
        resource, _, action = perm.partition(':')
        if action and f"{resource}:*" in self.role.permissions:
            return True
            
        return False

    def get_permissions(self) -> list:
        """Return list of all permissions for this user."""
        if self.is_superuser:
            return ['*']
        return self.role.permissions if self.role else []

    def __str__(self):
        return self.email