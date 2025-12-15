from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from core.models import (
    User, ModuleLabel, ModuleChoice, ModelChoice, FieldType, AssignmentRuleType
)
from core.forms import (
    ModuleLabelForm, ModuleChoiceForm, ModelChoiceForm, FieldTypeForm, AssignmentRuleTypeForm
)
from tenants.models import Tenant as TenantModel
from leads.models import Lead
from opportunities.models import Opportunity



def home(request):
    """
    Render the public landing page.
    """
    return render(request, 'public/index.html')


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

from django.views.generic import TemplateView




from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class AppSelectionView(LoginRequiredMixin, TemplateView):
    template_name = 'logged_in/app_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        from django.urls import reverse
        from core.apps_registry import AVAILABLE_APPS
        from accounts.models import RoleAppPermission
        
        # Initialize groups
        grouped_apps = {
            'customer': [],
            'work': [],
            'analytics': [],
            'admin': [],
            'control': []
        }
        
        has_any_apps = False
        
        # Fetch permissions if user has a role
        hidden_apps = set()
        if user.role and not user.is_superuser:
            permissions = RoleAppPermission.objects.filter(role=user.role)
            for perm in permissions:
                if not perm.is_visible:
                    hidden_apps.add(perm.app_identifier)

        for app in AVAILABLE_APPS:
            # Check visibility
            if app['id'] in hidden_apps:
                continue
                
            # Role/Permission logic (on top of DB permissions)
            # Superuser sees 'control' apps
            if app['category'] == 'control' and not user.is_superuser:
                continue
                
            # Add to group
            try:
                # Resolve URL
                url = reverse(app['url_name'])
                
                app_data = {
                    'name': app['name'],
                    'icon': app['icon'],
                    'url': url,
                    'id': app['id'] # Added ID for potential frontend use
                }
                
                grouped_apps[app['category']].append(app_data)
                has_any_apps = True
            except Exception:
                # Skip if URL reversal fails (e.g. app not installed/configured yet)
                pass

        context['grouped_apps'] = grouped_apps
        context['has_any_apps'] = has_any_apps
        context['user_info'] = {
            'name': user.get_full_name() or user.email,
            'company': user.tenant.name if user.tenant else 'SalesCompass Internal',
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
        from accounts.models import Role, RoleAppPermission
        
        roles = Role.objects.all()
        # Exclude control apps from configuration if desired, or keep them. 
        # Typically superuser stuff isn't toggled for other roles anyway because of logic in AppSelectionView.
        # Let's filter out 'control' category apps from being assigned to roles to avoid confusion.
        configurable_apps = [app for app in AVAILABLE_APPS if app['category'] != 'control']
        
        # Build a matrix of role -> app -> is_visible
        permission_matrix = {}
        
        all_perms = RoleAppPermission.objects.all()
        perm_lookup = {(p.role_id, p.app_identifier): p.is_visible for p in all_perms}
        
        for role in roles:
            role_perms = []
            for app in configurable_apps:
                # Default is True if not found
                is_visible = perm_lookup.get((role.id, app['id']), True)
                role_perms.append({
                    'app_id': app['id'],
                    'app_name': app['name'],
                    'is_visible': is_visible
                })
            permission_matrix[role] = role_perms

        context['configurable_apps'] = configurable_apps
        context['permission_matrix'] = permission_matrix
        return context

    def post(self, request, *args, **kwargs):
        from accounts.models import Role, RoleAppPermission
        
        # Process form submission
        # Expected format: perm_{role_id}_{app_id} = 'on' (if checked)
        # Any missing checked items means False? No, HTML checkboxes only send if checked.
        # But we need to handle "unchecking". 
        
        # Strategy: Iterate through all roles and apps, check if present in POST.
        
        from core.apps_registry import AVAILABLE_APPS
        configurable_apps = [app for app in AVAILABLE_APPS if app['category'] != 'control']
        roles = Role.objects.all()
        
        for role in roles:
            for app in configurable_apps:
                field_name = f"perm_{role.id}_{app['id']}"
                is_visible = request.POST.get(field_name) == 'on'
                
                # Update or create
                RoleAppPermission.objects.update_or_create(
                    role=role,
                    app_identifier=app['id'],
                    defaults={'is_visible': is_visible}
                )
        
        from django.contrib import messages
        messages.success(request, "App permissions updated successfully.")
        return self.get(request, *args, **kwargs)

# Module Label Views
class ModuleLabelListView(LoginRequiredMixin, ListView):
    model = ModuleLabel
    template_name = 'core/module_label_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        return ModuleLabel.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleLabelCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
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

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class ModuleLabelUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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


class ModuleLabelDeleteView(LoginRequiredMixin, DeleteView):
    model = ModuleLabel
    template_name = 'core/module_label_confirm_delete.html'
    success_url = reverse_lazy('core:module_label_list')

    def get_queryset(self):
        return ModuleLabel.objects.filter(tenant_id=self.request.user.tenant_id)


# Module Choice Views
class ModuleChoiceListView(LoginRequiredMixin, ListView):
    model = ModuleChoice
    template_name = 'core/module_choice_list.html'
    context_object_name = 'choices'

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleChoiceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'core/module_choice_form.html'
    success_message = "Module Choice created successfully."
    success_url = reverse_lazy('core:module_choice_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class ModuleChoiceUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'core/module_choice_form.html'
    success_message = "Module Choice updated successfully."
    success_url = reverse_lazy('core:module_choice_list')

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModuleChoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = ModuleChoice
    template_name = 'core/module_choice_confirm_delete.html'
    success_url = reverse_lazy('core:module_choice_list')

    def get_queryset(self):
        return ModuleChoice.objects.filter(tenant_id=self.request.user.tenant_id)


# Model Choice Views
class ModelChoiceListView(LoginRequiredMixin, ListView):
    model = ModelChoice
    template_name = 'core/model_choice_list.html'
    context_object_name = 'choices'

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModelChoiceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'core/model_choice_form.html'
    success_message = "Model Choice created successfully."
    success_url = reverse_lazy('core:model_choice_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class ModelChoiceUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'core/model_choice_form.html'
    success_message = "Model Choice updated successfully."
    success_url = reverse_lazy('core:model_choice_list')

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


class ModelChoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = ModelChoice
    template_name = 'core/model_choice_confirm_delete.html'
    success_url = reverse_lazy('core:model_choice_list')

    def get_queryset(self):
        return ModelChoice.objects.filter(tenant_id=self.request.user.tenant_id)


# Field Type Views
class FieldTypeListView(LoginRequiredMixin, ListView):
    model = FieldType
    template_name = 'core/field_type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


class FieldTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'core/field_type_form.html'
    success_message = "Field Type created successfully."
    success_url = reverse_lazy('core:field_type_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class FieldTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'core/field_type_form.html'
    success_message = "Field Type updated successfully."
    success_url = reverse_lazy('core:field_type_list')

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


class FieldTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = FieldType
    template_name = 'core/field_type_confirm_delete.html'
    success_url = reverse_lazy('core:field_type_list')

    def get_queryset(self):
        return FieldType.objects.filter(tenant_id=self.request.user.tenant_id)


# Assignment Rule Type Views
class AssignmentRuleTypeListView(LoginRequiredMixin, ListView):
    model = AssignmentRuleType
    template_name = 'core/assignment_rule_type_list.html'
    context_object_name = 'types'

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)


class AssignmentRuleTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'core/assignment_rule_type_form.html'
    success_message = "Assignment Rule Type created successfully."
    success_url = reverse_lazy('core:assignment_rule_type_list')

    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class AssignmentRuleTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'core/assignment_rule_type_form.html'
    success_message = "Assignment Rule Type updated successfully."
    success_url = reverse_lazy('core:assignment_rule_type_list')

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)


class AssignmentRuleTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = AssignmentRuleType
    template_name = 'core/assignment_rule_type_confirm_delete.html'
    success_url = reverse_lazy('core:assignment_rule_type_list')

    def get_queryset(self):
        return AssignmentRuleType.objects.filter(tenant_id=self.request.user.tenant_id)
