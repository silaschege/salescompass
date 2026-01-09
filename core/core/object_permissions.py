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

class ProductBundleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ProductBundle model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('products.*'):
            return queryset
        # Regular users with product permissions can view bundles
        return queryset.none()  # Or adjust as needed based on business logic

class CompetitorProductObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CompetitorProduct model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('products.*'):
            return queryset
        # Regular users with product permissions can view competitor products
        return queryset.none()  # Or adjust as needed based on business logic

class ProductComparisonObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ProductComparison model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('products.*'):
            return queryset
        # Regular users with product permissions can view product comparisons
        return queryset.none()  # Or adjust as needed based on business logic


class ProductDependencyObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ProductDependency model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('products.*'):
            return queryset
        # Regular users with product permissions can view product dependencies
        return queryset.none()  # Or adjust as needed based on business logic


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


class OpportunityStageObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for OpportunityStage model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Users can view stages in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('opportunities.*'):
            return queryset
        # Return only stages in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class PipelineTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PipelineType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Users can view pipeline types in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('opportunities.*'):
            return queryset
        # Return only pipeline types in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()




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




class CaseCommentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CaseComment model.
    A user can view/edit a comment if they have access to the associated case.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # User can view if they can access the related case
        from cases.models import Case
        try:
            case = Case.objects.get(pk=obj.case.pk)
            # Use the CaseObjectPolicy to check if user can access the case
            return CaseObjectPolicy.can_view(user, case)
        except Case.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow changing if user is the author and has case access
        if obj.author == user:
            from cases.models import Case
            try:
                case = Case.objects.get(pk=obj.case.pk)
                return CaseObjectPolicy.can_view(user, case)
            except Case.DoesNotExist:
                return False
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow deletion if user is the author and has case access
        if obj.author == user:
            from cases.models import Case
            try:
                case = Case.objects.get(pk=obj.case.pk)
                return CaseObjectPolicy.can_view(user, case)
            except Case.DoesNotExist:
                return False
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        
        # Filter to only comments from cases the user has access to
        # First get the cases the user can access
        from cases.models import Case
        accessible_cases = CaseObjectPolicy.get_viewable_queryset(user, Case.objects.all())
        
        # Then filter comments to only those from accessible cases
        return queryset.filter(case__in=accessible_cases)

class CaseAttachmentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CaseAttachment model.
    A user can view/edit an attachment if they have access to the associated case.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # User can view if they can access the related case
        from cases.models import Case
        try:
            case = Case.objects.get(pk=obj.case.pk)
            # Use the CaseObjectPolicy to check if user can access the case
            return CaseObjectPolicy.can_view(user, case)
        except Case.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow changing if user uploaded the attachment or has case access
        if obj.uploaded_by == user:
            from cases.models import Case
            try:
                case = Case.objects.get(pk=obj.case.pk)
                return CaseObjectPolicy.can_view(user, case)
            except Case.DoesNotExist:
                return False
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow deletion if user uploaded the attachment or has case access
        if obj.uploaded_by == user:
            from cases.models import Case
            try:
                case = Case.objects.get(pk=obj.case.pk)
                return CaseObjectPolicy.can_view(user, case)
            except Case.DoesNotExist:
                return False
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        
        # Filter to only attachments from cases the user has access to
        # First get the cases the user can access
        from cases.models import Case
        accessible_cases = CaseObjectPolicy.get_viewable_queryset(user, Case.objects.all())
        
        # Then filter attachments to only those from accessible cases
        return queryset.filter(case__in=accessible_cases)

class KnowledgeBaseArticleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for KnowledgeBaseArticle model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Anyone can view published articles
        if obj.is_published:
            return True
        # Author can view their articles
        if hasattr(obj, 'author') and obj.author == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Only author can change their articles
        if hasattr(obj, 'author') and obj.author == user:
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Only author can delete their articles
        if hasattr(obj, 'author') and obj.author == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        
        # Return published articles or articles authored by the user
        return queryset.filter(
            models.Q(is_published=True) |
            models.Q(author=user)
        )

class CsatSurveyObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CsatSurvey model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Users can view active surveys in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.change_csatsurvey'):
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.delete_csatsurvey'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        # Return only surveys in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class CsatResponseObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CsatResponse model.
    A user can view/edit a CSAT response if they have access to the associated case.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # User can view if they can access the related case
        from cases.models import Case
        try:
            case = Case.objects.get(pk=obj.case.pk)
            # Use the CaseObjectPolicy to check if user can access the case
            return CaseObjectPolicy.can_view(user, case)
        except Case.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow changing if user created the response or has case access
        from cases.models import Case
        try:
            case = Case.objects.get(pk=obj.case.pk)
            return CaseObjectPolicy.can_view(user, case)
        except Case.DoesNotExist:
            return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.delete_csatsurvey'):
            return True
        # Only allow deletion if user has access to the related case
        from cases.models import Case
        try:
            case = Case.objects.get(pk=obj.case.pk)
            return CaseObjectPolicy.can_view(user, case)
        except Case.DoesNotExist:
            return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        
        # Filter to only responses from cases the user has access to
        # First get the cases the user can access
        from cases.models import Case
        accessible_cases = CaseObjectPolicy.get_viewable_queryset(user, Case.objects.all())
        
        # Then filter responses to only those from accessible cases
        return queryset.filter(case__in=accessible_cases)

class CsatDetractorAlertObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CsatDetractorAlert model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # User can view if assigned to the alert or has access to the related case
        if obj.assigned_to == user:
            return True
        from cases.models import CsatResponse
        try:
            response = CsatResponse.objects.get(pk=obj.response.pk)
            case = response.case
            return CaseObjectPolicy.can_view(user, case)
        except CsatResponse.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Only allow changing if user is assigned to the alert
        if obj.assigned_to == user:
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.delete_csatdetractoralert'):
            return True
        # Only allow deletion if user is assigned to the alert
        if obj.assigned_to == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        
        # Filter to only alerts assigned to the user or from accessible cases
        # First get the cases the user can access
        from cases.models import Case, CsatResponse
        accessible_cases = CaseObjectPolicy.get_viewable_queryset(user, Case.objects.all())
        
        # Get responses from accessible cases
        accessible_responses = CsatResponse.objects.filter(case__in=accessible_cases)
        
        # Return alerts assigned to user or related to accessible responses
        return queryset.filter(
            models.Q(assigned_to=user) |
            models.Q(response__in=accessible_responses)
        )

class SlaPolicyObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SlaPolicy model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Users can view SLA policies in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.change_slapolicy'):
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.delete_slapolicy'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        # Return only SLA policies in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class CaseAssignmentRuleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AssignmentRule model (specific to cases).
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.*'):
            return True
        # Users can view assignment rules in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.change_assignmentrule'):
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('cases.delete_assignmentrule'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('cases.*'):
            return queryset
        # Return only assignment rules in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()



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




class TenantMemberObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for TenantMember model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('tenants.view_tenantmember'):
            return True
        if hasattr(user, 'tenant_member') and user.tenant_member.id == obj.id:
            return True
        if obj.manager_id == getattr(user, 'tenant_member_id', None):
            return True
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id') and user.tenant_id == obj.tenant_id:
             return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('tenants.change_tenantmember'):
            return True
        if obj.manager_id == getattr(user, 'tenant_member_id', None):
            return True
        return False

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('tenants.delete_tenantmember'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser:
            return queryset
        if user.has_perm('tenants.view_tenantmember'):
            return queryset
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class TenantRoleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for TenantRole model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('tenants.view_tenantrole'):
            return True
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id') and user.tenant_id == obj.tenant_id:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('tenants.view_tenantrole'):
            return queryset
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class TenantTerritoryObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for TenantTerritory model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('tenants.view_tenantterritory'):
            return True
        if hasattr(user, 'tenant_id') and hasattr(obj, 'tenant_id') and user.tenant_id == obj.tenant_id:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('tenants.view_tenantterritory'):
            return queryset
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()



class SaleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Sale model.
    """
    @classmethod
    def can_view(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('sales.*'):
            return True
        # Sales rep can view their sales
        if obj.sales_rep == user:
            return True
        # Account owner can view sales for their accounts
        if obj.account.owner == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('sales.*'):
            return True
        # Sales rep can change their sales
        if obj.sales_rep == user:
            return True
        # Account owner can change sales for their accounts
        if obj.account.owner == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('sales.*'):
            return queryset
        # Return sales where user is sales rep or account owner
        return queryset.filter(
            models.Q(sales_rep=user) |
            models.Q(account__owner=user)
        )


class AssignmentRuleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AssignmentRule model.
    """
    @classmethod
    def can_view(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Users can view assignment rules if they have general opportunities permissions
        return False

    @classmethod
    def can_change(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('opportunities.*'):
            return queryset
        # Regular users don't see assignment rules unless they have specific permissions
        return queryset.none()
    
class ProposalObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Proposal model.
    """
    @classmethod
    def can_view(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('proposals.*'):
            return True
        # Users with general proposals permissions can view proposals
        return False

    @classmethod
    def can_change(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('proposals.*'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('proposals.*'):
            return queryset
        # Regular users don't see proposals unless they have specific permissions
        return queryset.none()


class ProposalTemplateObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ProposalTemplate model.
    """
    @classmethod
    def can_view(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('proposals.*'):
            return True
        # Users with general proposals permissions can view templates
        return False

    @classmethod
    def can_change(cls, user: User, obj: any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('proposals.*'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('proposals.*'):
            return queryset
        # Regular users don't see templates unless they have specific permissions
        return queryset.none()








# Registry for easy lookup
OBJECT_POLICIES = {
    'core.User': UserObjectPolicy,
    'accounts.Account': AccountObjectPolicy,
    'accounts.Contact': ContactObjectPolicy,
    'leads.Lead': LeadsObjectPolicy,
    'leads.WebToLeadForm': LeadsObjectPolicy,
    'products.Product': ProductsObjectPolicy,
    'products.ProductBundle': ProductBundleObjectPolicy,
    'products.CompetitorProduct': CompetitorProductObjectPolicy,
    'products.ProductDependency': ProductDependencyObjectPolicy,
    'products.ProductComparison': ProductComparisonObjectPolicy,
    'opportunities.Opportunity': OpportunitiesObjectPolicy,
    'opportunities.OpportunityStage': OpportunityStageObjectPolicy,
    'opportunities.Opportunity': OpportunityObjectPolicy,
    'opportunities.PipelineType': PipelineTypeObjectPolicy,
    'opportunities.AssignmentRule': AssignmentRuleObjectPolicy,
    'proposals.Proposal': ProposalObjectPolicy,
    'proposals.ProposalTemplate': ProposalTemplateObjectPolicy,
    
    'cases.Case': CaseObjectPolicy,
    'cases.CaseComment': CaseCommentObjectPolicy,
    'cases.CaseAttachment': CaseAttachmentObjectPolicy,
    'cases.KnowledgeBaseArticle': KnowledgeBaseArticleObjectPolicy,
    'cases.CsatSurvey': CsatSurveyObjectPolicy,
    'cases.CsatResponse': CsatResponseObjectPolicy,
    'cases.CsatDetractorAlert': CsatDetractorAlertObjectPolicy,
    'cases.SlaPolicy': SlaPolicyObjectPolicy,
    'cases.AssignmentRule': CaseAssignmentRuleObjectPolicy,  # Assignment rules specific to cases
    'marketing.MarketingCampaign': MarketingCampaignObjectPolicy,
    'team.TeamMember': TeamObjectPolicy,
    'learn.Article': LearnObjectPolicy,
    
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
    'sales.Sale': SaleObjectPolicy,

    'tenants.TenantMember': TenantMemberObjectPolicy,
    'tenants.TenantRole': TenantRoleObjectPolicy,
    'tenants.TenantTerritory': TenantTerritoryObjectPolicy,
}