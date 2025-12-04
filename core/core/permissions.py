from typing import Optional
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from django.http import HttpRequest
from core.models import User

# === Django View Permission Decorator ===
def require_permission(perm: str):
    """
    Decorator for function-based views.
    
    Usage:
        @require_permission('accounts:read')
        def account_list(request):
            ...
    """
    def decorator(view_func):
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            if not request.user.has_perm(perm):
                raise PermissionDenied(f"Missing required permission: {perm}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# === Class-Based View Mixin ===
class PermissionRequiredMixin:
    """
    Mixin for class-based views.
    
    Usage:
        class AccountListView(PermissionRequiredMixin, ListView):
            required_permission = 'accounts:read'
    """
    required_permission: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")
        if self.required_permission and not request.user.has_perm(self.required_permission):
            raise PermissionDenied(f"Missing required permission: {self.required_permission}")
        return super().dispatch(request, *args, **kwargs)


# === Object-Level Permission Mixin ===
class ObjectPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Mixin for class-based views that enforces object-level permissions.
    
    Usage:
        class AccountDetailView(ObjectPermissionRequiredMixin, DetailView):
            model = Account
            object_permission_policy = AccountObjectPolicy  # optional; auto-detected if omitted
    """
    object_permission_policy = None
    permission_action = 'view'  # 'view', 'change', 'delete'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        policy = self.get_object_policy()
        
        user = self.request.user
        action = self.permission_action
        
        if action == 'view' and not policy.can_view(user, obj):
            raise PermissionDenied("You do not have permission to view this object.")
        elif action == 'change' and not policy.can_change(user, obj):
            raise PermissionDenied("You do not have permission to edit this object.")
        elif action == 'delete' and not policy.can_delete(user, obj):
            raise PermissionDenied("You do not have permission to delete this object.")
            
        return obj

    def get_queryset(self):
        """Apply viewable filter to list views."""
        qs = super().get_queryset()
        policy = self.get_object_policy()
        if policy:
            return policy.get_viewable_queryset(self.request.user, qs)
        return qs

    def get_object_policy(self):
        if self.object_permission_policy:
            return self.object_permission_policy
        from core.object_permissions import OBJECT_POLICIES
        key = f"{self.model._meta.app_label}.{self.model._meta.object_name}"
        policy = OBJECT_POLICIES.get(key)
        if not policy:
            raise NotImplementedError(
                f"No object permission policy registered for {self.model}. "
                "Register it in core.object_permissions.OBJECT_POLICIES"
            )
        return policy


# === DRF Permission Class ===
class HasPermission(BasePermission):
    """
    DRF-compatible permission class.
    
    Usage in ViewSets:
        class AccountViewSet(viewsets.ModelViewSet):
            permission_classes = [HasPermission]
            required_permission = 'accounts:read'  # or set per action
    """
    def has_permission(self, request, view):
        # Allow safe methods for OPTIONS
        if request.method == 'OPTIONS':
            return True

        perm = getattr(view, 'required_permission', None)
        if not perm:
            # If no permission required, allow
            return True

        if not request.user.is_authenticated:
            return False

        return request.user.has_perm(perm)

    def has_object_permission(self, request, view, obj):
        # Object-level permissions not implemented here
        # Extend if needed (e.g., ownership check)
        return True