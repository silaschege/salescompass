
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from core.apps_registry import SUPERUSER_ONLY_CATEGORIES, AVAILABLE_APPS
from core.models import (
    User, ModuleLabel, ModuleChoice, ModelChoice, FieldType, AssignmentRuleType,
    SystemConfigType, SystemConfigCategory, SystemEventType, SystemEventSeverity,
    HealthCheckType, HealthCheckStatus, MaintenanceStatus, MaintenanceType,
    PerformanceMetricType, PerformanceEnvironment, NotificationType, NotificationPriority
) 
from core.forms import (
    ModuleLabelForm, ModuleChoiceForm, ModelChoiceForm, FieldTypeForm, AssignmentRuleTypeForm
)
from tenants.models import Tenant as TenantModel, TenantFeatureEntitlement
from leads.models import Lead
from opportunities.models import Opportunity


class TenantAwareViewMixin:
    """
    Mixin to filter querysets by the current user's tenant.
    This ensures data isolation in multi-tenant environments.
    """
    def get_queryset(self):
        # Allow views to define a base queryset
        if hasattr(super(), 'get_queryset'):
            queryset = super().get_queryset()
        elif hasattr(self, 'model') and self.model:
            queryset = self.model.objects.all()
        else:
             # Fallback or error, but let's assume usage in generic views
             return None 
             
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            # Only filter if the model actually has a tenant field to avoid FieldErrors
            # for global models (like WorkflowTemplate)
            from django.core.exceptions import FieldDoesNotExist
            try:
                # Use queryset.model to ensure we're checking the actual model being queried
                # This is safer than self.model which might be None in some generic views
                model = queryset.model
                
                # Check for 'tenant' field (standard FK in TenantModel)
                model._meta.get_field('tenant')
                return queryset.filter(tenant_id=self.request.user.tenant_id)
            except FieldDoesNotExist:
                try:
                    # Fallback: check for direct 'tenant_id' field
                    model._meta.get_field('tenant_id')
                    return queryset.filter(tenant_id=self.request.user.tenant_id)
                except FieldDoesNotExist:
                    # Model is not tenant-aware, return unfiltered queryset
                    pass
                    
        return queryset

    def get_form_kwargs(self):
        """
        Inject tenant into form kwargs if available.
        This allows forms to filter dynamic choices by tenant.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            # Fetch the actual Tenant object if needed by the form, or just pass the ID
            # Based on LeadsForm, it expects 'tenant' object (or at least something with .id)
            # For efficiency we might just pass the user.tenant object if available
            # Assuming user.tenant is available via relation
            if hasattr(self.request.user, 'tenant'):
                 kwargs['tenant'] = self.request.user.tenant
        return kwargs


# --- Standardized Base Views ---

class SalesCompassListView(LoginRequiredMixin, TenantAwareViewMixin, ListView):
    """
    Standard List View for SalesCompass apps.
    Enforces Login and Tenant Scoping.
    """
    pass


class SalesCompassDetailView(LoginRequiredMixin, TenantAwareViewMixin, DetailView):
    """
    Standard Detail View for SalesCompass apps.
    Enforces Login and Tenant Scoping.
    """
    pass


class SalesCompassCreateView(LoginRequiredMixin, SuccessMessageMixin, TenantAwareViewMixin, CreateView):
    """
    Standard Create View for SalesCompass apps.
    Enforces Login, Tenant Scoping, and automatic Tenant assignment.
    """
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
             # Handle both direct field assignment and object assignment if needed
             if hasattr(form.instance, 'tenant_id'):
                form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class SalesCompassUpdateView(LoginRequiredMixin, SuccessMessageMixin, TenantAwareViewMixin, UpdateView):
    """
    Standard Update View for SalesCompass apps.
    Enforces Login and Tenant Scoping.
    """
    pass


class SalesCompassDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    """
    Standard Delete View for SalesCompass apps.
    Enforces Login and Tenant Scoping.
    """
    pass


# --- Authentication Views ---

def logout_view(request):
    """
    Custom logout view that logs out the user and redirects to the home page.
    """
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    
    logout(request)
    return redirect('core:home')

def home(request):
    """
    Render the public landing page.
    """
    return render(request, 'public/index.html')


# --- Dashboard Views ---

@login_required
def clv_dashboard(request):
    """
    Display the Customer Lifetime Value (CLV) dashboard with key metrics.
    """
    # Calculate overall CLV metrics
    users = User.objects.all()
    
    # Calculate average CLV
    avg_clv = users.aggregate(avg_clv=Avg('customer_lifetime_value'))['avg_clv'] or 0
    
    # Calculate total CLV
    total_clv = users.aggregate(total_clv=Sum('customer_lifetime_value'))['total_clv'] or 0
    
    # Calculate average order value
    avg_order_value = users.aggregate(avg_order=Avg('avg_order_value'))['avg_order'] or 0
    
    # Calculate average purchase frequency
    avg_purchase_frequency = users.aggregate(avg_freq=Avg('purchase_frequency'))['avg_freq'] or 0
    
    # Get top customers by CLV
    top_customers = users.order_by('-customer_lifetime_value')[:10]
    
    # Calculate CLV trend (simplified - just showing how it could be done)
    clv_trend_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    clv_trend_data = [1000, 1200, 1100, 1300, 1400, 1500]  # Placeholder data
    
    context = {
        'avg_clv': avg_clv,
        'total_clv': total_clv,
        'avg_order_value': avg_order_value,
        'avg_purchase_frequency': avg_purchase_frequency,
        'top_customers': top_customers,
        'clv_trend_labels': clv_trend_labels,
        'clv_trend_data': clv_trend_data,
    }
    
    return render(request, 'core/clv_dashboard.html', context)


def calculate_clv_simple(request):
    """
    Calculate CLV using the simple formula: Average Order Value × Purchase Frequency × Customer Lifespan
    """
    # This would typically be called from a model method
    pass


# --- Application Selection Views ---

from access_control.controller import UnifiedAccessController

class AppSelectionView(LoginRequiredMixin, TemplateView):
    template_name = 'logged_in/app_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 1. Define which CATEGORIES are strictly for Superusers
        # Based on your registry, 'control' contains infrastructure, audit logs, etc.
        # Add 'core' here only if you want to hide Home/Dashboard from standard users.
        RESTRICTED_CATEGORIES = ['control'] 

        # Initialize groups to match your AVAILABLE_APPS 'category' keys
        grouped_apps = {
            'core': [],
            'feature': [],
            'control': []
        }
        
        has_any_apps = False
        
        # 2. Get accessible resources via Unified Access Control
        # This handles entitlements, feature flags, and permissions in one go
        accessible_feature_keys = set()
        if not user.is_superuser:
            available_resources = UnifiedAccessController.get_available_resources(user)
            accessible_feature_keys = {r['key'] for r in available_resources}

        # Apps that are always available if the URL reverses
        ALWAYS_VISIBLE_APPS = ['home', 'dashboard']

        for app in AVAILABLE_APPS:
            app_id = app['id']
            app_category = app['category']

            # --- CHECK 1: Tenant Feature Entitlements & Permissions via Unified Access Control ---
            # If it's not a core app and not explicitly in accessible features, skip it for non-superusers
            # We allow superusers to see everything regardless of tenant features for overrides/debugging
            if not user.is_superuser and app_id not in ALWAYS_VISIBLE_APPS:
                if app_id not in accessible_feature_keys:
                    continue
                
            # --- CHECK 4: Add to group if URL resolves ---
            try:
                url = reverse(app['url_name'])
                
                app_data = {
                    'name': app['name'],
                    'icon': app['icon'],
                    'url': url,
                    'id': app_id,
                    'description': app.get('description', '')
                }
                
                if app_category in grouped_apps:
                    grouped_apps[app_category].append(app_data)
                    has_any_apps = True
                    
            except Exception:
                # Skip if URL reversal fails
                pass

        context['grouped_apps'] = grouped_apps
        context['has_any_apps'] = has_any_apps
        context['user_info'] = {
            'name': user.get_full_name() or user.email,
            'company': getattr(user.tenant, 'name', 'SalesCompass Internal') if hasattr(user, 'tenant') else 'SalesCompass Internal',
            'role': 'Superuser' if user.is_superuser else (user.role.name if user.role else 'Standard User')
        }
            
        return context

class AppSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'logged_in/app_settings.html'
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.apps_registry import AVAILABLE_APPS
        from access_control.role_models import Role
        from access_control.models import AccessControl
        
        roles = Role.objects.all()
        # Include ALL apps for configuration, including control apps
        configurable_apps = AVAILABLE_APPS
        
        # Build a matrix of role -> app -> is_visible using AccessControl
        permission_matrix = {}
        
        all_perms = AccessControl.objects.filter(
            scope_type='role',
            access_type='permission'
        )
        perm_lookup = {(p.role_id, p.key): p.is_enabled for p in all_perms}
        
        for role in roles:
            role_perms = []
            for app in configurable_apps:
                # Default is True if not found
                is_visible = perm_lookup.get((role.id, app['id']), True)
                role_perms.append({
                    'app_id': app['id'],
                    'app_name': app['name'],
                    'category': app['category'],  # Pass category for grouping in template
                    'icon': app['icon'],          # Pass icon for UI
                    'is_visible': is_visible
                })
            permission_matrix[role] = role_perms

        context['configurable_apps'] = configurable_apps
        context['permission_matrix'] = permission_matrix
        return context

    def post(self, request, *args, **kwargs):
        from access_control.role_models import Role
        from access_control.models import AccessControl
        
        # Process form submission
        # Expected format: perm_{role_id}_{app_id} = 'on' (if checked)
        
        from core.apps_registry import AVAILABLE_APPS
        # Use ALL apps
        configurable_apps = AVAILABLE_APPS
        roles = Role.objects.all()
        
        for role in roles:
            for app in configurable_apps:
                field_name = f"perm_{role.id}_{app['id']}"
                is_visible = request.POST.get(field_name) == 'on'
                
                # Update or create using AccessControl
                AccessControl.objects.update_or_create(
                    key=app['id'],
                    scope_type='role',
                    role=role,
                    access_type='permission',
                    defaults={
                        'name': f"{app['name']} Permission",
                        'is_enabled': is_visible
                    }
                )
        
        from django.contrib import messages
        messages.success(request, "App permissions updated successfully.")
        return self.get(request, *args, **kwargs)


# --- Module Management Views ---

# Module Label Views
class ModuleLabelListView(SalesCompassListView):
    model = ModuleLabel
    template_name = 'core/module_label_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        return ModuleLabel.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleLabelCreateView(SalesCompassCreateView):
    model = ModuleLabel
    form_class = ModuleLabelForm
    template_name = 'core/module_label_form.html'
    success_message = "Module Label created successfully."
    success_url = reverse_lazy('core:module_label_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs


class ModuleLabelUpdateView(SalesCompassUpdateView):
    model = ModuleLabel
    form_class = ModuleLabelForm
    template_name = 'core/module_label_form.html'
    success_message = "Module Label updated successfully."
    success_url = reverse_lazy('core:module_label_list')

    def get_queryset(self):
        return ModuleLabel.objects.filter(tenant_id=self.request.user.tenant_id)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs


class ModuleLabelDeleteView(SalesCompassDeleteView):
    model = ModuleLabel
    template_name = 'core/module_label_confirm_delete.html'
    success_url = reverse_lazy('core:module_label_list')

    def get_queryset(self):
        return ModuleLabel.objects.filter(tenant_id=self.request.user.tenant_id)


# Module Choice Views
class ModuleChoiceListView(SalesCompassListView):
    model = ModuleChoice
    template_name = 'core/module_choice_list.html'
    context_object_name = 'choices'

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleChoiceCreateView(SalesCompassCreateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'core/module_choice_form.html'
    success_message = "Module Choice created successfully."
    success_url = reverse_lazy('core:module_choice_list')


class ModuleChoiceUpdateView(SalesCompassUpdateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'core/module_choice_form.html'
    success_message = "Module Choice updated successfully."
    success_url = reverse_lazy('core:module_choice_list')

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleChoiceDeleteView(SalesCompassDeleteView):
    model = ModuleChoice
    template_name = 'core/module_choice_confirm_delete.html'
    success_url = reverse_lazy('core:module_choice_list')

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


# Model Choice Views
class ModelChoiceListView(SalesCompassListView):
    model = ModelChoice
    template_name = 'core/model_choice_list.html'
    context_object_name = 'choices'

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModelChoiceCreateView(SalesCompassCreateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'core/model_choice_form.html'
    success_message = "Model Choice created successfully."
    success_url = reverse_lazy('core:model_choice_list')


class ModelChoiceUpdateView(SalesCompassUpdateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'core/model_choice_form.html'
    success_message = "Model Choice updated successfully."
    success_url = reverse_lazy('core:model_choice_list')

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModelChoiceDeleteView(SalesCompassDeleteView):
    model = ModelChoice
    template_name = 'core/model_choice_confirm_delete.html'
    success_url = reverse_lazy('core:model_choice_list')

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


# Field Type Views
class FieldTypeListView(SalesCompassListView):
    model = FieldType
    template_name = 'core/field_type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


class FieldTypeCreateView(SalesCompassCreateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'core/field_type_form.html'
    success_message = "Field Type created successfully."
    success_url = reverse_lazy('core:field_type_list')


class FieldTypeUpdateView(SalesCompassUpdateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'core/field_type_form.html'
    success_message = "Field Type updated successfully."
    success_url = reverse_lazy('core:field_type_list')

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


class FieldTypeDeleteView(SalesCompassDeleteView):
    model = FieldType
    template_name = 'core/field_type_confirm_delete.html'
    success_url = reverse_lazy('core:field_type_list')

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


# Assignment Rule Type Views
class AssignmentRuleTypeListView(SalesCompassListView):
    model = AssignmentRuleType
    template_name = 'core/assignment_rule_type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)


class AssignmentRuleTypeCreateView(SalesCompassCreateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'core/assignment_rule_type_form.html'
    success_message = "Assignment Rule Type created successfully."
    success_url = reverse_lazy('core:assignment_rule_type_list')


class AssignmentRuleTypeUpdateView(SalesCompassUpdateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'core/assignment_rule_type_form.html'
    success_message = "Assignment Rule Type updated successfully."
    success_url = reverse_lazy('core:assignment_rule_type_list')

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)


class AssignmentRuleTypeDeleteView(SalesCompassDeleteView):
    model = AssignmentRuleType
    template_name = 'core/assignment_rule_type_confirm_delete.html'
    success_url = reverse_lazy('core:assignment_rule_type_list')

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)