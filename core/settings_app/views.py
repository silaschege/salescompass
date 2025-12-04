from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DeleteView, DetailView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from core.permissions import PermissionRequiredMixin
from core.object_permissions import TeamObjectPolicy 
from .utils import onboard_new_team_member
from .forms import TeamRoleForm
from django import forms
import logging

# Import models from settings_app
from .models import (
    SettingGroup, Setting, Territory, TeamRole, TeamMember,
    CustomField, ModuleLabel, AssignmentRule, PipelineStage, 
    APIKey, Webhook, BehavioralScoringRule, DemographicScoringRule, ScoreDecayConfig
)

# Import models from other apps
from leads.models import LeadStatus, LeadSource
from opportunities.models import OpportunityStage
from tenants.models import Tenant

logger = logging.getLogger(__name__)

# --- Settings Dashboard ---

class SettingsDashboardView(PermissionRequiredMixin, TemplateView):
    template_name = 'settings_app/dashboard.html'
    required_permission = 'settings_app:read'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for dashboard cards (ensure models are available in the scope)
        context['custom_fields_count'] = self.get_model_count('CustomField')
        context['module_labels_count'] = self.get_model_count('ModuleLabel')
        context['assignment_rules_count'] = self.get_model_count('AssignmentRule')
        context['pipeline_stages_count'] = self.get_model_count('PipelineStage')
        context['api_keys_count'] = self.get_model_count('APIKey')
        context['webhooks_count'] = self.get_model_count('Webhook')
        context['team_members_count'] = self.get_model_count('TeamMember')
        
        return context
    
    def get_model_count(self, model_name):
        """Helper to get count of records for a model, specific to tenant"""
        try:
            # Use globals() to access the explicitly imported model classes
            model_class = globals().get(model_name)
            if model_class:
                 return model_class.objects.filter(tenant_id=self.request.user.tenant_id).count()
        except Exception as e:
            logger.error(f"Error getting count for model {model_name}: {e}")
            pass
        return 0

# --- General CRM Settings (Dynamic Key-Value Store) ---

class CrmSettingsListView(PermissionRequiredMixin, ListView):
    model = SettingGroup
    template_name = 'settings_app/crm_settings_list.html'
    context_object_name = 'groups'
    required_permission = 'settings_app:read'

    def get_queryset(self):
        # Filter for the current tenant's settings groups
        return super().get_queryset().prefetch_related('settings').filter(tenant_id=self.request.user.tenant_id)


class CrmSettingsUpdateView(PermissionRequiredMixin, UpdateView):
    model = Setting
    fields = []  # Handled dynamically in form
    template_name = 'settings_app/crm_settings_form.html'
    required_permission = 'settings_app:write'

    def get_form(self, form_class=None):
        from .forms import DynamicSettingForm, TeamRoleForm
        return DynamicSettingForm(**self.get_form_kwargs())

    def get_success_url(self):
        return reverse('settings_app:list')

# --- Tenant Settings (Placeholders for your TenantSettingsView) ---
# Assuming this handles the branding/locale fields added to the Tenant model
class TenantSettingsView(PermissionRequiredMixin, UpdateView):
    # This view requires you to define a form or fields related to your Tenant model
    fields = ['name', 'domain', 'logo', 'primary_color', 'secondary_color', 'business_hours', 'default_currency', 'date_format', 'time_zone'] 
    model = Tenant # Import Tenant model from tenants.models
    template_name = 'settings_app/tenant_settings_form.html'
    success_url = reverse_lazy('settings_app:tenant_settings')
    required_permission = 'settings_app:write'
    
    def get_object(self, queryset=None):
        # Gets the specific tenant object for the logged-in user
        return get_object_or_404(Tenant, id=self.request.user.tenant_id)


# --- Team Management ---

class TeamListView(PermissionRequiredMixin, ListView):
    model = TeamMember
    template_name = 'settings_app/teams_list.html'
    context_object_name = 'team_members'
    paginate_by = 20
    required_permission = 'settings_app:read'

    def get_queryset(self):
        # Filter for the current tenant
        return super().get_queryset().select_related('user', 'role', 'manager', 'territory').filter(user__tenant_id=self.request.user.tenant_id)


class TeamDetailView(PermissionRequiredMixin, DetailView):
    model = TeamMember
    template_name = 'settings_app/team_detail.html'
    context_object_name = 'member'
    required_permission = 'settings_app:read'

    def get_queryset(self):
        return super().get_queryset().select_related('user', 'role', 'manager', 'territory').filter(user__tenant_id=self.request.user.tenant_id)


class TeamCreateView(PermissionRequiredMixin, CreateView):
    model = TeamMember
    fields = ['user', 'role', 'manager', 'territory', 'phone', 'hire_date', 'quota_amount', 'quota_period']
    template_name = 'settings_app/team_form.html'
    success_url = reverse_lazy('settings_app:team_list')
    required_permission = 'settings_app:write'

    def form_valid(self, form):
        # Ensure user being added belongs to the same tenant (basic validation)
        user_to_add = form.cleaned_data['user']
        if user_to_add.tenant_id != self.request.user.tenant_id:
             form.add_error('user', 'Cannot add a user from a different tenant.')
             return self.form_invalid(form)
             
        response = super().form_valid(form)
        onboard_new_team_member(form.instance.user.id)
        return response
    
class TeamUpdateView(PermissionRequiredMixin, UpdateView):
    model = TeamMember
    fields = ['role', 'manager', 'territory', 'phone', 'hire_date', 'quota_amount', 'quota_period']
    template_name = 'settings_app/team_form.html'
    required_permission = 'settings_app:write'
    permission_policy = TeamObjectPolicy # Apply object-level permissions
    
    def get_success_url(self):
        return reverse('settings_app:team_list')

class TeamDeleteView(PermissionRequiredMixin, DeleteView):
    model = TeamMember
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:team_list')
    required_permission = 'settings_app:write'
    permission_policy = TeamObjectPolicy
    
    def get_queryset(self):
        return super().get_queryset().filter(user__tenant_id=self.request.user.tenant_id)


# --- Territories ---

class TerritoryListView(PermissionRequiredMixin, ListView):
    model = Territory
    template_name = 'settings_app/territory_list.html'
    context_object_name = 'territories'
    required_permission = 'settings_app:read'

    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)

class TerritoryCreateView(PermissionRequiredMixin, CreateView):
    model = Territory
    fields = ['name', 'description', 'country_codes']
    template_name = 'settings_app/territory_form.html'
    success_url = reverse_lazy('settings_app:territory_list')
    required_permission = 'settings_app:write'
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)

class TerritoryUpdateView(PermissionRequiredMixin, UpdateView):
    model = Territory
    fields = ['name', 'description', 'country_codes']
    template_name = 'settings_app/territory_form.html'
    success_url = reverse_lazy('settings_app:territory_list')
    required_permission = 'settings_app:write'

class TerritoryDeleteView(PermissionRequiredMixin, DeleteView):
    model = Territory
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:territory_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)


# --- Quotas ---

class QuotaUpdateView(PermissionRequiredMixin, UpdateView):
    model = TeamMember
    fields = ['quota_amount', 'quota_period']
    template_name = 'settings_app/quota_form.html'
    required_permission = 'settings_app:write'

    def get_object(self, queryset=None):
        team_member_id = self.kwargs.get('team_member_id')
        # Ensure object belongs to the tenant before editing
        return get_object_or_404(TeamMember, id=team_member_id, user__tenant_id=self.request.user.tenant_id)

    def get_success_url(self):
        return reverse('settings_app:team_list')

# --- Roles & Permissions ---

class RoleListView(PermissionRequiredMixin, ListView):
    # Assuming TeamRole is your tenant-specific role model
    model = TeamRole 
    template_name = 'settings_app/role_list.html'
    context_object_name = 'roles'
    required_permission = 'settings_app:read'
    
    def get_queryset(self):
        return self.model.objects.filter(tenant_id=self.request.user.tenant_id)


class RoleCreateView(PermissionRequiredMixin, CreateView):
    model = TeamRole
    template_name = 'settings_app/role_form.html'
    form_class = TeamRoleForm
    template_name = 'settings_app/role_form.html'
    required_permission = 'settings_app:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = ['accounts', 'leads', 'opportunities', 'contacts', 'settings', 'reports', 'team', 'territories', 'quotas', 'api_keys', 'webhooks']
        context['actions'] = ['read', 'write', 'delete', 'manage']
        return context

    def get_success_url(self):
        return reverse('settings_app:role_list')
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)

class RoleUpdateView(PermissionRequiredMixin, UpdateView):
    model = TeamRole
    template_name = 'settings_app/role_form.html'
    form_class = TeamRoleForm
    template_name = 'settings_app/role_form.html'
    required_permission = 'settings_app:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = ['accounts', 'leads', 'opportunities', 'contacts', 'settings', 'reports', 'team', 'territories', 'quotas', 'api_keys', 'webhooks']
        context['actions'] = ['read', 'write', 'delete', 'manage']
        return context

    def get_success_url(self):
        return reverse('settings_app:role_list')

class RoleDeleteView(PermissionRequiredMixin, DeleteView):
    model = TeamRole
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:role_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)


# --- Lead Settings (Placeholders) ---

class LeadStatusListView(PermissionRequiredMixin, ListView):
    model = LeadStatus
    template_name = 'settings_app/lead_status_list.html'
    context_object_name = 'statuses'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class LeadStatusCreateView(PermissionRequiredMixin, CreateView):
    model = LeadStatus
    fields = ['name', 'is_active']
    template_name = 'settings_app/lead_status_form.html'
    success_url = reverse_lazy('settings_app:lead_status_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class LeadStatusUpdateView(PermissionRequiredMixin, UpdateView):
    model = LeadStatus
    fields = ['name', 'is_active']
    template_name = 'settings_app/lead_status_form.html'
    success_url = reverse_lazy('settings_app:lead_status_list')
    required_permission = 'settings_app:write'

class LeadStatusDeleteView(PermissionRequiredMixin, DeleteView):
    model = LeadStatus
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:lead_status_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)

class LeadSourceListView(PermissionRequiredMixin, ListView):
    model = LeadSource
    template_name = 'settings_app/lead_source_list.html'
    context_object_name = 'sources'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class LeadSourceCreateView(PermissionRequiredMixin, CreateView):
    model = LeadSource
    fields = ['name','label','order','color', 'icon', 'is_active', 'conversion_rate_target']
    template_name = 'settings_app/lead_source_form.html'
    success_url = reverse_lazy('settings_app:lead_source_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)

class LeadSourceUpdateView(PermissionRequiredMixin, UpdateView):
    model = LeadSource
    fields = ['name','label','order','color', 'icon', 'is_active', 'conversion_rate_target']
    template_name = 'settings_app/lead_source_form.html'
    success_url = reverse_lazy('settings_app:lead_source_list')
    required_permission = 'settings_app:write'

class LeadSourceDeleteView(PermissionRequiredMixin, DeleteView):
    model = LeadSource
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:lead_source_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Opportunity Settings (Placeholders) ---

class OpportunityStageListView(PermissionRequiredMixin, ListView):
    model = OpportunityStage
    template_name = 'settings_app/opportunity_stage_list.html'
    context_object_name = 'stages'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class OpportunityStageCreateView(PermissionRequiredMixin, CreateView):
    model = OpportunityStage
    fields = ['name', 'order', 'win_probability', 'is_active']
    template_name = 'settings_app/opportunity_stage_form.html'
    success_url = reverse_lazy('settings_app:opportunity_stage_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class OpportunityStageUpdateView(PermissionRequiredMixin, UpdateView):
    model = OpportunityStage
    fields = ['name', 'order', 'win_probability', 'is_active']
    template_name = 'settings_app/opportunity_stage_form.html'
    success_url = reverse_lazy('settings_app:opportunity_stage_list')
    required_permission = 'settings_app:write'

class OpportunityStageDeleteView(PermissionRequiredMixin, DeleteView):
    model = OpportunityStage
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:opportunity_stage_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Custom Fields (Fixes the original Attribute Error) ---

class CustomFieldListView(PermissionRequiredMixin, ListView):
    model = CustomField
    template_name = 'settings_app/custom_field_list.html'
    context_object_name = 'custom_fields'
    required_permission = 'settings_app:read'
    def get_queryset(self):
        return CustomField.objects.filter(tenant_id=self.request.user.tenant_id)

class CustomFieldCreateView(PermissionRequiredMixin, CreateView):
    model = CustomField
    template_name = 'settings_app/custom_field_form.html'
    fields = ['model_name', 'field_name', 'field_label', 'field_type', 'is_required', 'options', 'help_text', 'default_value']
    success_url = reverse_lazy('settings_app:custom_field_list')
    required_permission = 'settings_app:write'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create Custom Field'
        return context
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        
        # Parse options from textarea (one per line) if it's a select field
        if form.cleaned_data['field_type'] == 'select':
            options_text = self.request.POST.get('options', '')
            if options_text:
                options_list = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                form.instance.options = options_list
        
        return super().form_valid(form)


class CustomFieldUpdateView(PermissionRequiredMixin, UpdateView):
    model = CustomField
    template_name = 'settings_app/custom_field_form.html'
    fields = ['field_label', 'field_type', 'is_required', 'options', 'help_text', 'default_value']
    success_url = reverse_lazy('settings_app:custom_field_list')
    required_permission = 'settings_app:write'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Edit Custom Field: {self.object.field_label}'
        return context
    
    def form_valid(self, form):
        # Parse options from textarea if it's a select field
        if form.cleaned_data['field_type'] == 'select':
            options_text = self.request.POST.get('options', '')
            if options_text:
                options_list = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                form.instance.options = options_list
        
        return super().form_valid(form)


# --- Module Labels (Placeholders) ---

class CustomFieldDeleteView(PermissionRequiredMixin, DeleteView):
    model = CustomField
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:custom_field_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        # Ensure only tenant's custom fields can be deleted
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)


class ModuleLabelListView(PermissionRequiredMixin, ListView):
    model = ModuleLabel
    template_name = 'settings_app/module_label_list.html'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class ModuleLabelCreateView(PermissionRequiredMixin, CreateView):
    model = ModuleLabel
    fields = ['module_key', 'custom_label']
    template_name = 'settings_app/module_label_form.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class ModuleLabelUpdateView(PermissionRequiredMixin, UpdateView):
    model = ModuleLabel
    fields = ['custom_label']
    template_name = 'settings_app/module_label_form.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    required_permission = 'settings_app:write'

class ModuleLabelDeleteView(PermissionRequiredMixin, DeleteView):
    model = ModuleLabel
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Assignment Rules (Placeholders) ---

class AssignmentRuleListView(PermissionRequiredMixin, ListView):
    model = AssignmentRule
    template_name = 'settings_app/assignment_rule_list.html'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class AssignmentRuleCreateView(PermissionRequiredMixin, CreateView):
    model = AssignmentRule
    fields = ['module', 'rule_type', 'criteria', 'assignees', 'is_active']
    template_name = 'settings_app/assignment_rule_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class AssignmentRuleUpdateView(PermissionRequiredMixin, UpdateView):
    model = AssignmentRule
    fields = ['rule_type', 'criteria', 'assignees', 'is_active']
    template_name = 'settings_app/assignment_rule_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    required_permission = 'settings_app:write'

class AssignmentRuleDeleteView(PermissionRequiredMixin, DeleteView):
    model = AssignmentRule
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Pipeline Stages (Placeholders) ---

class PipelineStageListView(PermissionRequiredMixin, ListView):
    model = PipelineStage
    template_name = 'settings_app/pipeline_stage_list.html'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class PipelineStageCreateView(PermissionRequiredMixin, CreateView):
    model = PipelineStage
    fields = ['pipeline_type', 'name', 'order', 'required_fields', 'approval_required']
    template_name = 'settings_app/pipeline_stage_form.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class PipelineStageUpdateView(PermissionRequiredMixin, UpdateView):
    model = PipelineStage
    fields = ['name', 'order', 'required_fields', 'approval_required']
    template_name = 'settings_app/pipeline_stage_form.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    required_permission = 'settings_app:write'

class PipelineStageDeleteView(PermissionRequiredMixin, DeleteView):
    model = PipelineStage
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- API Keys (Placeholders) ---

class APIKeyListView(PermissionRequiredMixin, ListView):
    model = APIKey
    template_name = 'settings_app/apikey_list.html'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class APIKeyCreateView(PermissionRequiredMixin, CreateView):
    model = APIKey
    fields = ['name', 'scopes']
    template_name = 'settings_app/apikey_form.html'
    success_url = reverse_lazy('settings_app:apikey_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; form.instance.key_hash = 'GENERATED_HASH'; return super().form_valid(form)

class APIKeyDeleteView(PermissionRequiredMixin, DeleteView):
    model = APIKey
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:apikey_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Webhooks (Placeholders) ---

class WebhookListView(PermissionRequiredMixin, ListView):
    model = Webhook
    template_name = 'settings_app/webhook_list.html'
    required_permission = 'settings_app:read'
    def get_queryset(self): return self.model.objects.filter(tenant_id=self.request.user.tenant_id)
class WebhookCreateView(PermissionRequiredMixin, CreateView):
    model = Webhook
    fields = ['url', 'events', 'secret', 'is_active']
    template_name = 'settings_app/webhook_form.html'
    success_url = reverse_lazy('settings_app:webhook_list')
    required_permission = 'settings_app:write'
    def form_valid(self, form): form.instance.tenant_id = self.request.user.tenant_id; return super().form_valid(form)
class WebhookUpdateView(PermissionRequiredMixin, UpdateView):
    model = Webhook
    fields = ['url', 'events', 'is_active']
    template_name = 'settings_app/webhook_form.html'
    success_url = reverse_lazy('settings_app:webhook_list')
    required_permission = 'settings_app:write'

class WebhookDeleteView(PermissionRequiredMixin, DeleteView):
    model = Webhook
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:webhook_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)



# --- Lead Scoring Rules ---

class ScoringRulesListView(PermissionRequiredMixin, TemplateView):
    """Combined list view for all scoring rules."""
    template_name = 'settings_app/scoring_rules_list.html'
    required_permission = 'settings_app:read'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.user.tenant_id
        
        context['behavioral_rules'] = BehavioralScoringRule.objects.filter(
            tenant_id=tenant_id
        ).order_by('-priority', 'name')
        
        context['demographic_rules'] = DemographicScoringRule.objects.filter(
            tenant_id=tenant_id
        ).order_by('-priority', 'name')
        
        context['decay_config'] = ScoreDecayConfig.objects.filter(
            tenant_id=tenant_id
        ).first()
        
        return context


class BehavioralScoringRuleCreateView(PermissionRequiredMixin, CreateView):
    """Create behavioral scoring rule."""
    model = BehavioralScoringRule
    template_name = 'settings_app/behavioral_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_form_class(self):
        from .forms import BehavioralScoringRuleForm
        return BehavioralScoringRuleForm
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class BehavioralScoringRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """Update behavioral scoring rule."""
    model = BehavioralScoringRule
    template_name = 'settings_app/behavioral_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_form_class(self):
        from .forms import BehavioralScoringRuleForm
        return BehavioralScoringRuleForm

class BehavioralScoringRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete behavioral scoring rule."""
    model = BehavioralScoringRule
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)
    
    def get_form_class(self):
        from .forms import BehavioralScoringRuleForm
        return BehavioralScoringRuleForm


class DemographicScoringRuleCreateView(PermissionRequiredMixin, CreateView):
    """Create demographic scoring rule."""
    model = DemographicScoringRule
    template_name = 'settings_app/demographic_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_form_class(self):
        from .forms import DemographicScoringRuleForm
        return DemographicScoringRuleForm
    
    def form_valid(self, form):
        form.instance.tenant_id = self.request.user.tenant_id
        return super().form_valid(form)


class DemographicScoringRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """Update demographic scoring rule."""
    model = DemographicScoringRule
    template_name = 'settings_app/demographic_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_form_class(self):
        from .forms import DemographicScoringRuleForm
        return DemographicScoringRuleForm

class DemographicScoringRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete demographic scoring rule."""
    model = DemographicScoringRule
    template_name = 'settings_app/confirm_delete.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_queryset(self):
        return super().get_queryset().filter(tenant_id=self.request.user.tenant_id)
    
    def get_form_class(self):
        from .forms import DemographicScoringRuleForm
        return DemographicScoringRuleForm


class ScoreDecayConfigView(PermissionRequiredMixin, UpdateView):
    """Configure score decay (single config per tenant)."""
    model = ScoreDecayConfig
    template_name = 'settings_app/score_decay_config.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')
    required_permission = 'settings_app:write'
    
    def get_form_class(self):
        from .forms import ScoreDecayConfigForm
        return ScoreDecayConfigForm
    
    def get_object(self, queryset=None):
        # Get or create the decay config for this tenant
        config, created = ScoreDecayConfig.objects.get_or_create(
            tenant_id=self.request.user.tenant_id
        )
        return config

