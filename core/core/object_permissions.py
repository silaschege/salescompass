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


class SupplierObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Supplier model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('products.*') or user.has_perm('purchasing.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('products.*') or user.has_perm('purchasing.*'):
            return queryset
        return queryset.none()


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

class PurchasingObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Purchasing models.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('purchasing.*'):
            return True
        return False
    
    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('purchasing.*'):
            return queryset
        return queryset.none()


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
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('opportunities.*'):
            return True
        # Owner can change their opportunities
        if obj.owner == user:
            return True
        # Account owner can change opportunities for their accounts
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
        if user.has_perm('cases.delete_csatsurvey'):
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
        accessible_cases = CaseObjectPolicy.get_viewable_queryset(
            user, Case.objects.all()
        )
        
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

class CampaignStatusObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CampaignStatus model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view campaign statuses in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only campaign statuses in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class EmailProviderObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EmailProvider model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view email providers in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only email providers in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class SegmentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Segment model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their segments
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only segments created by the user
        return queryset.filter(created_by=user)

class SegmentMemberObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for SegmentMember model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view segment members in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only segment members in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class BlockTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for BlockType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view block types in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only block types in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class EmailCategoryObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EmailCategory model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view email categories in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only email categories in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class MessageTypeObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for MessageType model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view message types in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only message types in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class MessageCategoryObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for MessageCategory model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view message categories in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only message categories in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class EmailTemplateObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EmailTemplate model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their email templates
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only email templates created by the user
        return queryset.filter(created_by=user)

class LandingPageObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for LandingPage model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their landing pages
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only landing pages created by the user
        return queryset.filter(created_by=user)

class LandingPageBlockObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for LandingPageBlock model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view landing page blocks in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only landing page blocks in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class MessageTemplateObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for MessageTemplate model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their message templates
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only message templates created by the user
        return queryset.filter(created_by=user)

class EmailCampaignObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EmailCampaign model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their email campaigns
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only email campaigns created by the user
        return queryset.filter(created_by=user)

class CampaignRecipientObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CampaignRecipient model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Users can view campaign recipients in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only campaign recipients in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()

class ABAutomatedTestObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ABAutomatedTest model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their A/B tests
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only A/B tests created by the user
        return queryset.filter(created_by=user)

class EmailIntegrationObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EmailIntegration model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # User can view their email integrations
        return obj.user == user

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only email integrations belonging to the user
        return queryset.filter(user=user)

class ABTestObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ABTest model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('marketing.*'):
            return True
        # Owner can view their A/B tests
        if obj.created_by == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.has_perm('marketing.*'):
            return queryset
        # Return only A/B tests created by the user
        return queryset.filter(created_by=user)


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


# Object policies for automation models
class WorkflowObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Workflow model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflows
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_workflow'):
            return True
        # Only allow changing if user has tenant access and created the workflow
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id and obj.created_by == user

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_workflow'):
            return True
        # Only allow deletion if user has tenant access and created the workflow
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id and obj.created_by == user

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflows in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowActionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowAction model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflow actions
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow actions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowBranchObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowBranch model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflow branches
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow branches in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowExecutionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowExecution model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflow executions
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow executions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowTriggerObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowTrigger model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflow triggers
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow triggers in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowTemplateObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowTemplate model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users with tenant access can view workflow templates
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow templates in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationAlertObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationAlert model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view alerts in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_automationalert'):
            return True
        # Only allow changing if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_automationalert'):
            return True
        # Only allow deletion if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automation alerts in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationNotificationPreferenceObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationNotificationPreference model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view preferences for their user/tenant
        return obj.user == user and obj.tenant == user.tenant

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_automationnotificationpreference'):
            return True
        # Only allow changing preferences for their user/tenant
        return obj.user == user and obj.tenant == user.tenant

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_automationnotificationpreference'):
            return True
        # Only allow deletion of preferences for their user/tenant
        return obj.user == user and obj.tenant == user.tenant

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only notification preferences for the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowApprovalObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowApproval model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view approvals in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_workflowapproval'):
            return True
        # Only allow changing if user is the requester or assigned
        return obj.approval_requester == user or obj.requested_approvers.filter(pk=user.pk).exists()

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_workflowapproval'):
            return True
        # Only allow deletion if user is the requester or assigned
        return obj.approval_requester == user or obj.requested_approvers.filter(pk=user.pk).exists()

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow approvals in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowScheduledExecutionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowScheduledExecution model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view scheduled executions in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_workflowscheduledexecution'):
            return True
        # Only allow changing if user is the creator
        return obj.created_by == user

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_workflowscheduledexecution'):
            return True
        # Only allow deletion if user is the creator
        return obj.created_by == user

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only scheduled executions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowVersionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowVersion model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view versions in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_workflowversion'):
            return True
        # Only allow changing if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_workflowversion'):
            return True
        # Only allow deletion if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow versions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WorkflowAnalyticsSnapshotObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WorkflowAnalyticsSnapshot model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view analytics in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_workflowanalyticssnapshot'):
            return True
        # Only allow changing if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_workflowanalyticssnapshot'):
            return True
        # Only allow deletion if user has tenant access
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only workflow analytics snapshots in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class CustomCodeSnippetObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CustomCodeSnippet model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view snippets in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_customcodesnippet'):
            return True
        # Only allow changing if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_customcodesnippet'):
            return True
        # Only allow deletion if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only custom code snippets in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class CustomCodeExecutionLogObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for CustomCodeExecutionLog model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view logs in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only custom code execution logs in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for Automation model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view automations in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_automation'):
            return True
        # Only allow changing if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_automation'):
            return True
        # Only allow deletion if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automations in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationConditionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationCondition model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view conditions in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automation conditions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationActionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationAction model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view actions in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automation actions in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationExecutionLogObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationExecutionLog model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view logs in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automation execution logs in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WebhookEndpointObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WebhookEndpoint model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view webhook endpoints in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_webhookendpoint'):
            return True
        # Only allow changing if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_webhookendpoint'):
            return True
        # Only allow deletion if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only webhook endpoints in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class AutomationRuleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutomationRule model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view rules in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_automationrule'):
            return True
        # Only allow changing if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_automationrule'):
            return True
        # Only allow deletion if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only automation rules in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class WebhookDeliveryLogObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WebhookDeliveryLog model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view delivery logs in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only webhook delivery logs in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class QualityCheckScheduleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for QualityCheckSchedule model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.*'):
            return True
        # Users can view schedules in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.change_qualitycheckschedule'):
            return True
        # Only allow changing if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_delete(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('automation.delete_qualitycheckschedule'):
            return True
        # Only allow deletion if user is the creator and has tenant access
        return obj.created_by == user and hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('automation.*'):
            return queryset
        # Return only quality check schedules in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


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


class EngagementEventObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementEvent model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view events related to accounts they own or have access to
        if obj.account and obj.account == user:
            return True
        if obj.account_company and hasattr(obj.account_company, 'owner') and obj.account_company.owner == user:
            return True
        if obj.lead and obj.lead.owner == user:
            return True
        if obj.contact and obj.contact.account.owner == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Only superusers and users with general engagement perms can change events
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return events related to accounts, leads, or contacts the user has access to
        return queryset.filter(
            models.Q(account=user) |
            models.Q(account_company__owner=user) |
            models.Q(lead__owner=user) |
            models.Q(contact__account__owner=user)
        )


class EngagementStatusObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementStatus model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view their own engagement status
        if obj.account == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can change their own engagement status
        if obj.account == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only the user's own engagement status
        return queryset.filter(account=user)


class NextBestActionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for NextBestAction model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view actions assigned to them or related to their accounts
        if obj.assigned_to == user:
            return True
        if obj.account == user:
            return True
        if obj.opportunity and obj.opportunity.owner == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can change actions assigned to them
        if obj.assigned_to == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return actions assigned to the user or related to accounts/opportunities they have access to
        return queryset.filter(
            models.Q(assigned_to=user) |
            models.Q(account=user) |
            models.Q(opportunity__owner=user)
        )


class AutoNBARuleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for AutoNBARule model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view rules in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_autonbarule'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only rules in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class EngagementWebhookObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementWebhook model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view webhooks in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementwebhook'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only webhooks in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class EngagementWorkflowObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementWorkflow model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view workflows in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementworkflow'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only workflows in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class EngagementWorkflowExecutionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementWorkflowExecution model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view executions related to their accounts or in their tenant
        if obj.account == user:
            return True
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementworkflowexecution'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return executions for the user's account or in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(
                models.Q(account=user) |
                models.Q(tenant_id=user.tenant_id)
            )
        return queryset.none()


class EngagementPlaybookObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementPlaybook model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view playbooks in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementplaybook'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only playbooks in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class PlaybookStepObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PlaybookStep model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view steps of playbooks in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.playbook.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_playbookstep'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only steps of playbooks in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(playbook__tenant_id=user.tenant_id)
        return queryset.none()


class PlaybookExecutionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PlaybookExecution model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view executions related to their accounts or in their tenant
        if obj.account == user:
            return True
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_playbookexecution'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return executions for the user's account or in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(
                models.Q(account=user) |
                models.Q(tenant_id=user.tenant_id)
            )
        return queryset.none()


class PlaybookStepExecutionObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for PlaybookStepExecution model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view step executions related to their accounts or in their tenant
        if obj.playbook_execution.account == user:
            return True
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_playbookstepexecution'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return step executions for the user's account or in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(
                models.Q(playbook_execution__account=user) |
                models.Q(tenant_id=user.tenant_id)
            )
        return queryset.none()


class EngagementEventCommentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementEventComment model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view comments they made or comments on events they can access
        if obj.user == user:
            return True
        # Check if user can access the related engagement event
        from engagement.models import EngagementEvent
        try:
            event = EngagementEvent.objects.get(pk=obj.engagement_event.pk)
            from . import EngagementEventObjectPolicy
            return EngagementEventObjectPolicy.can_view(user, event)
        except EngagementEvent.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow changing if user is the author
        if obj.user == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return comments made by the user or comments on events the user can access
        # First get the events the user can access
        from engagement.models import EngagementEvent
        accessible_events = EngagementEventObjectPolicy.get_viewable_queryset(
            user, EngagementEvent.objects.all()
        )
        
        # Then filter comments to only those on accessible events or made by the user
        return queryset.filter(
            models.Q(user=user) |
            models.Q(engagement_event__in=accessible_events)
        )


class NextBestActionCommentObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for NextBestActionComment model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view comments they made or comments on actions they can access
        if obj.user == user:
            return True
        # Check if user can access the related next best action
        from engagement.models import NextBestAction
        try:
            action = NextBestAction.objects.get(pk=obj.next_best_action.pk)
            from . import NextBestActionObjectPolicy
            return NextBestActionObjectPolicy.can_view(user, action)
        except NextBestAction.DoesNotExist:
            return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        # Only allow changing if user is the author
        if obj.user == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return comments made by the user or comments on actions the user can access
        # First get the actions the user can access
        from engagement.models import NextBestAction
        accessible_actions = NextBestActionObjectPolicy.get_viewable_queryset(
            user, NextBestAction.objects.all()
        )
        
        # Then filter comments to only those on accessible actions or made by the user
        return queryset.filter(
            models.Q(user=user) |
            models.Q(next_best_action__in=accessible_actions)
        )


class ScoringRuleObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for ScoringRule model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view rules in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_scoringrule'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only rules in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class EngagementScoringConfigObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementScoringConfig model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view configs in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementscoringconfig'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only configs in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


class EngagementScoreSnapshotObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for EngagementScoreSnapshot model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view snapshots of their own accounts
        if obj.account == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_engagementscoresnapshot'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only snapshots for the user's account
        return queryset.filter(account=user)


class WebhookDeliveryLogObjectPolicy(ObjectPermissionPolicy):
    """
    Object-level permission policy for WebhookDeliveryLog model.
    """
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.*'):
            return True
        # Users can view logs in their tenant
        return hasattr(user, 'tenant_id') and user.tenant_id == obj.tenant_id

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('engagement.change_webhookdeliverylog'):
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('engagement.*'):
            return queryset
        # Return only logs in the user's tenant
        if hasattr(user, 'tenant_id'):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()


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
        # Account owner can view sales for their account
        if hasattr(obj.account, 'owner') and obj.account.owner == user:
            return True
        return False

    @classmethod
    def can_change(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('sales.*'):
            return True
        # Sales rep can change their sales
        if obj.sales_rep == user:
            return True
        # Account owner can change sales for their account
        if hasattr(obj.account, 'owner') and obj.account.owner == user:
            return True
        return False

    @classmethod
    def _get_policy_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('sales.*'):
            return queryset
        # Return sales where user is sales rep or where user is the account owner
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
    'products.ProductCategory': ProductsObjectPolicy,
    'products.ProductBundle': ProductBundleObjectPolicy,
    'products.CompetitorProduct': CompetitorProductObjectPolicy,
    'products.ProductComparison': ProductComparisonObjectPolicy,
    'products.ProductDependency': ProductDependencyObjectPolicy,
    'products.Supplier': SupplierObjectPolicy,
    'purchasing.PurchaseOrder': PurchasingObjectPolicy,
    'purchasing.SupplierInvoice': PurchasingObjectPolicy,
    'purchasing.GoodsReceipt': PurchasingObjectPolicy,
    'purchasing.SupplierPayment': PurchasingObjectPolicy,
    'opportunities.Opportunity': OpportunityObjectPolicy,
    'opportunities.OpportunityStage': OpportunityStageObjectPolicy,
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
    
    # Engagement models
    'engagement.EngagementEvent': EngagementEventObjectPolicy,
    'engagement.EngagementStatus': EngagementStatusObjectPolicy,
    'engagement.NextBestAction': NextBestActionObjectPolicy,
    'engagement.AutoNBARule': AutoNBARuleObjectPolicy,
    'engagement.EngagementWebhook': EngagementWebhookObjectPolicy,
    'engagement.EngagementWorkflow': EngagementWorkflowObjectPolicy,
    'engagement.EngagementWorkflowExecution': EngagementWorkflowExecutionObjectPolicy,
    'engagement.EngagementPlaybook': EngagementPlaybookObjectPolicy,
    'engagement.PlaybookStep': PlaybookStepObjectPolicy,
    'engagement.PlaybookExecution': PlaybookExecutionObjectPolicy,
    'engagement.PlaybookStepExecution': PlaybookStepExecutionObjectPolicy,
    'engagement.EngagementEventComment': EngagementEventCommentObjectPolicy,
    'engagement.NextBestActionComment': NextBestActionCommentObjectPolicy,
    'engagement.ScoringRule': ScoringRuleObjectPolicy,
    'engagement.EngagementScoringConfig': EngagementScoringConfigObjectPolicy,
    'engagement.EngagementScoreSnapshot': EngagementScoreSnapshotObjectPolicy,
    'engagement.WebhookDeliveryLog': WebhookDeliveryLogObjectPolicy,
    
    # Marketing models
    'marketing.CampaignStatus': CampaignStatusObjectPolicy,
    'marketing.EmailProvider': EmailProviderObjectPolicy,
    'marketing.Segment': SegmentObjectPolicy,
    'marketing.SegmentMember': SegmentMemberObjectPolicy,
    'marketing.BlockType': BlockTypeObjectPolicy,
    'marketing.EmailCategory': EmailCategoryObjectPolicy,
    'marketing.MessageType': MessageTypeObjectPolicy,
    'marketing.MessageCategory': MessageCategoryObjectPolicy,
    'marketing.Campaign': MarketingCampaignObjectPolicy,
    'marketing.EmailTemplate': EmailTemplateObjectPolicy,
    'marketing.LandingPage': LandingPageObjectPolicy,
    'marketing.LandingPageBlock': LandingPageBlockObjectPolicy,
    'marketing.MessageTemplate': MessageTemplateObjectPolicy,
    'marketing.EmailCampaign': EmailCampaignObjectPolicy,
    'marketing.CampaignRecipient': CampaignRecipientObjectPolicy,
    'marketing.ABAutomatedTest': ABAutomatedTestObjectPolicy,
    'marketing.EmailIntegration': EmailIntegrationObjectPolicy,
    'marketing.ABTest': ABTestObjectPolicy,
    
    # Automation models
    'automation.Workflow': WorkflowObjectPolicy,
    'automation.WorkflowAction': WorkflowActionObjectPolicy,
    'automation.WorkflowBranch': WorkflowBranchObjectPolicy,
    'automation.WorkflowExecution': WorkflowExecutionObjectPolicy,
    'automation.WorkflowTrigger': WorkflowTriggerObjectPolicy,
    'automation.WorkflowTemplate': WorkflowTemplateObjectPolicy,
    'automation.AutomationAlert': AutomationAlertObjectPolicy,
    'automation.AutomationNotificationPreference': AutomationNotificationPreferenceObjectPolicy,
    'automation.WorkflowApproval': WorkflowApprovalObjectPolicy,
    'automation.WorkflowScheduledExecution': WorkflowScheduledExecutionObjectPolicy,
    'automation.WorkflowVersion': WorkflowVersionObjectPolicy,
    'automation.WorkflowAnalyticsSnapshot': WorkflowAnalyticsSnapshotObjectPolicy,
    'automation.CustomCodeSnippet': CustomCodeSnippetObjectPolicy,
    'automation.CustomCodeExecutionLog': CustomCodeExecutionLogObjectPolicy,
    'automation.Automation': AutomationObjectPolicy,
    'automation.AutomationCondition': AutomationConditionObjectPolicy,
    'automation.AutomationAction': AutomationActionObjectPolicy,
    'automation.AutomationExecutionLog': AutomationExecutionLogObjectPolicy,
    'automation.WebhookEndpoint': WebhookEndpointObjectPolicy,
    'automation.AutomationRule': AutomationRuleObjectPolicy,
    'automation.WebhookDeliveryLog': WebhookDeliveryLogObjectPolicy,
    'automation.QualityCheckSchedule': QualityCheckScheduleObjectPolicy,
}