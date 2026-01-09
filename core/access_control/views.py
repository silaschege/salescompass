from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .controller import UnifiedAccessController

class SecureViewMixin:
    """
    Mixin for securing views with unified access control
    """
    required_access = None  # Set in subclass
    access_action = 'access'  # Default action
    
    def dispatch(self, request, *args, **kwargs):
        if not self.required_access:
            return super().dispatch(request, *args, **kwargs)
        
        if not UnifiedAccessController.has_access(
            request.user, 
            self.required_access, 
            self.access_action
        ):
            raise PermissionDenied("You don't have access to this resource")
        
        return super().dispatch(request, *args, **kwargs)

class DashboardView(SecureViewMixin, LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    required_access = 'dashboard.view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available apps for user
        available_resources = UnifiedAccessController.get_available_resources(
            self.request.user
        )
        
        context.update({
            'available_resources': available_resources,
        })
        
        return context
