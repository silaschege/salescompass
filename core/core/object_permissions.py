from typing import Any, Type
from django.db import models
from core.models import User
from django.contrib.auth.mixins import UserPassesTestMixin


class WidgetTypePermissionMixin(UserPassesTestMixin):
    """Permission mixin for WidgetType views - checks user has dashboard permissions."""
    
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        if user.has_perm('dashboard.view_widgettype') or user.has_perm('dashboard.*'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id'):
            return True
        return False


class WidgetCategoryPermissionMixin(UserPassesTestMixin):
    """Permission mixin for WidgetCategory views - checks user has dashboard permissions."""
    
    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        if user.has_perm('dashboard.view_widgetcategory') or user.has_perm('dashboard.*'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id'):
            return True
        return False


class ObjectPermissionPolicy:
    """
    Base class for defining object-level access rules.
    
    Subclass per model to define:
      - can_view(user, obj)
      - can_change(user, obj)
      - can_delete(user, obj)
      - get_viewable_queryset(user, queryset)
    """
    
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        """Return True if user can view this object."""
        raise NotImplementedError

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        """Return True if user can edit this object."""
        return cls.can_view(user, obj)  # by default, view implies edit for many models

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        """Return True if user can delete this object."""
        return cls.can_change(user, obj)

    @classmethod
    def get_viewable_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        """
        Return filtered queryset of objects the user can view.
        Must be efficient (use Q objects, not Python loops).
        """
        # 1. Superuser sees all
        if user.is_superuser:
            return queryset
            
        # 2. Enforce Tenant Isolation
        if hasattr(user, 'tenant_id') and user.tenant_id:
            # Ensure model has tenant_id field (or handle gracefully)
            # We assume most models here are TenantModels
            if hasattr(queryset.model, 'tenant_id'):
                queryset = queryset.filter(tenant_id=user.tenant_id)
        
        return cls._get_policy_queryset(user, queryset)

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        """
        Subclasses implement specific logic here (after tenant filter).
        """
        raise NotImplementedError

class AccountObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Account model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('accounts.*'):
            return True
        # Owner can view their accounts
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('accounts.*'):
            return queryset
        # Return only accounts owned by the user
        return queryset.filter(owner=user)



class LeadsObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Leads model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('leads.*'):
            return True
        # Owner can view their leads
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('leads.*'):
            return queryset
        # Return only leads owned by the user
        return queryset.filter(owner=user)

class ProductsObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Products model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*'):
            return True
        # Owner can view their products
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('products.*'):
            return queryset
        # Return only product owned by the user
        return queryset.filter(owner=user)

class OpportunitiesObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for opportunities model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Owner can view their opportunities
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('opportunities.*'):
            return queryset
        # Return only opportunities owned by the user
        return queryset.filter(owner=user)

# Add the Opportunity policy here
class OpportunityObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for opportunities model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Owner can view their opportunities
        if obj.owner == user:
            return True
        # Account owner can view opportunities for their accounts
        if hasattr(obj, 'account') and obj.account.owner == user:
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('opportunities.*'):
            return queryset
        # Return opportunities owned by user OR opportunities for accounts owned by user
        return queryset.filter(
            models.Q(owner=user) | 
            models.Q(account__owner=user)
        )

class ProposalObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for proposals model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('proposals.*'):
            return True
        # Sent by user can view their proposals
        if obj.sent_by == user:
            return True
        # Owner of related opportunity can view proposals
        if hasattr(obj, 'opportunity') and hasattr(obj.opportunity, 'owner') and obj.opportunity.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('proposals.*'):
            return queryset
        # Return only proposals sent by the user or for opportunities they own
        return queryset.filter(
            models.Q(sent_by=user) | 
            models.Q(opportunity__owner=user)
        )

class CaseObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for cases model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Owner can view their cases
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('cases.*'):
            return queryset
        # Return only cases owned by the user
        return queryset.filter(owner=user)

class MarketingCampaignObjectPolicy(ObjectPermissionPolicy):
    """ 
    Object-level permission policy for marketing model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their marketing
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only marketing owned by the user
        return queryset.filter(owner=user)

class TeamObjectPolicy(ObjectPermissionPolicy):
    """ 
    Object-level permission policy for teamMember model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('teamMember.*'):
            return True
        # Owner can view their teamMember
        if obj.owner == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('teamMember.*'):
            return queryset
        # Return only teamMember owned by the user
        return queryset.filter(owner=user)

class LearnObjectPolicy(ObjectPermissionPolicy):
    """ 
    Object-level permission policy for article model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('article.*'):
            return True
        # Public articles can be viewed by anyone
        if obj.is_public:
            return True
        # Author can view their article
        if obj.author == user:
            return True
        return False
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('article.*'):
            return queryset
        # Return public articles or articles authored by the user
        return queryset.filter(
            models.Q(is_public=True) | 
            models.Q(author=user)
        )


class ContactObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Contact model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('accounts.*'):
            return True
        # Owner of the account can view contacts
        if obj.account.owner == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('accounts.*'):
            return queryset
        # Return contacts for accounts owned by the user
        return queryset.filter(account__owner=user)


# Dynamic Choice Model Policies
class SystemConfigTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SystemConfigType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_systemconfigtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_systemconfigtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_systemconfigtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class SystemConfigCategoryObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SystemConfigCategory model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_systemconfigcategory'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_systemconfigcategory'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_systemconfigcategory'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class SystemEventTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SystemEventType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_systemeventtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_systemeventtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_systemeventtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class SystemEventSeverityObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SystemEventSeverity model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_systemeventseverity'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_systemeventseverity'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_systemeventseverity'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class HealthCheckTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for HealthCheckType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_healthchecktype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_healthchecktype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_healthchecktype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class HealthCheckStatusObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for HealthCheckStatus model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_healthcheckstatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_healthcheckstatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_healthcheckstatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class MaintenanceStatusObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for MaintenanceStatus model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_maintenancestatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_maintenancestatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_maintenancestatus'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class MaintenanceTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for MaintenanceType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_maintenancetype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_maintenancetype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_maintenancetype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class PerformanceMetricTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PerformanceMetricType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_performancemetrictype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_performancemetrictype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_performancemetrictype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class PerformanceEnvironmentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PerformanceEnvironment model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_performanceenvironment'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_performanceenvironment'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_performanceenvironment'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class NotificationTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for NotificationType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_notificationtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_notificationtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_notificationtype'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset


class NotificationPriorityObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for NotificationPriority model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.view_notificationpriority'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.change_notificationpriority'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('core.delete_notificationpriority'):
            return True
        # Check tenant isolation
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id'):
            return user.tenant_id == obj.tenant_id
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('core.*'):
            return queryset
        # Apply tenant isolation
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset

class UserObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for User model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('auth.view_user'):
            return True
        # Users can view their own user object
        if obj == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('auth.*'):
            return queryset
        # Return only the user's own user object
        return queryset.filter(id=user.id)

# In core/object_permissions.py

class OrganizationMemberObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for OrganizationMember model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        # Superusers can view all organization members
        if user.is_superuser:
            return True
        # Users with specific permission can view
        if user.has_perm('accounts.view_organizationmember'):
            return True
        # Users can view their own membership
        if hasattr(user, 'organization_membership') and user.organization_membership == obj:
            return True
        # Users can view their direct reports
        if obj.manager == getattr(user, 'organization_membership', None):
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        # Superusers can change all organization members
        if user.is_superuser:
            return True
        # Users with specific permission can change
        if user.has_perm('accounts.change_organizationmember'):
            return True
        # Managers can change their direct reports
        if obj.manager == getattr(user, 'organization_membership', None):
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        # Only superusers can delete organization members
        if user.is_superuser:
            return True
        # Users with specific permission can delete
        if user.has_perm('accounts.delete_organizationmember'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        # Superusers see all organization members
        if user.is_superuser:
            return queryset
        
        # Users with specific permission see all
        if user.has_perm('accounts.*'):
            return queryset
            
        # Regular users only see themselves and their direct reports
        if hasattr(user, 'organization_membership'):
            return queryset.filter(
                models.Q(id=user.organization_membership.id) |  # Themselves
                models.Q(manager=user.organization_membership)   # Their direct reports
            )
        
        # Users without organization membership can't see any
        return queryset.none()


# Registry for easy lookup
OBJECT_POLICIES = {
    'core.User': UserObjectPolicy,
    'accounts.Account': AccountObjectPolicy,
    'accounts.Contact': ContactObjectPolicy,
    'leads.Lead': LeadsObjectPolicy,
    'leads.WebToLeadForm': LeadsObjectPolicy,
    'products.Product': ProductsObjectPolicy,
    'opportunities.Opportunity': OpportunitiesObjectPolicy,
    'opportunities.Opportunity': OpportunityObjectPolicy,
    'proposals.Proposal': ProposalObjectPolicy,
    'cases.Case': CaseObjectPolicy,
    'marketing.MarketingCampaign': MarketingCampaignObjectPolicy,
    'team.TeamMember': TeamObjectPolicy,
    'learn.Article': LearnObjectPolicy,
    # Dynamic choice model policies
    'core.SystemConfigType': SystemConfigTypeObjectPolicy,
    'core.SystemConfigCategory': SystemConfigCategoryObjectPolicy,
    'core.SystemEventType': SystemEventTypeObjectPolicy,
    'core.SystemEventSeverity': SystemEventSeverityObjectPolicy,
    'core.HealthCheckType': HealthCheckTypeObjectPolicy,
    'core.HealthCheckStatus': HealthCheckStatusObjectPolicy,
    'core.MaintenanceStatus': MaintenanceStatusObjectPolicy,
    'core.MaintenanceType': MaintenanceTypeObjectPolicy,
    'core.PerformanceMetricType': PerformanceMetricTypeObjectPolicy,
    'core.PerformanceEnvironment': PerformanceEnvironmentObjectPolicy,
    'core.NotificationType': NotificationTypeObjectPolicy,
    'core.NotificationPriority': NotificationPriorityObjectPolicy,
}
