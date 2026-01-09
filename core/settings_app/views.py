from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.urls import reverse_lazy
from .models import Setting, CustomField, ModuleLabel, AssignmentRule, PipelineStage, EmailIntegration, BehavioralScoringRule, DemographicScoringRule, SettingType, ModelChoice, FieldType, ModuleChoice, AssignmentRuleType, PipelineType, EmailProvider, ActionType, OperatorType, SettingGroup
from sales.models import SalesTarget
from commissions.models import Quota
from .forms import SettingForm, CustomFieldForm, ModuleLabelForm, AssignmentRuleForm, PipelineStageForm, EmailIntegrationForm, BehavioralScoringRuleForm, DemographicScoringRuleForm, SettingTypeForm, ModelChoiceForm, FieldTypeForm, ModuleChoiceForm, AssignmentRuleTypeForm, PipelineTypeForm, EmailProviderForm, ActionTypeForm, OperatorTypeForm
from tenants.models import Tenant as TenantModel


class SettingsDashboardView(TemplateView):
    """Settings dashboard landing page."""
    template_name = 'settings_app/dashboard.html'


class CrmSettingsListView(ListView):
    """List CRM settings."""
    model = Setting
    template_name = 'settings_app/crm_settings_list.html'
    context_object_name = 'settings'


class CrmSettingsUpdateView(UpdateView):
    """Update CRM settings."""
    model = Setting
    form_class = SettingForm
    template_name = 'settings_app/crm_settings_form.html'
    success_url = reverse_lazy('settings_app:list')


class TenantSettingsView(TemplateView):
    """Tenant-specific settings."""
    template_name = 'settings_app/tenant_settings.html'








class LeadStatusListView(TemplateView):
    """Lead status settings - placeholder."""
    template_name = 'settings_app/lead_status_list.html'


class LeadStatusCreateView(TemplateView):
    """Create lead status - placeholder."""
    template_name = 'settings_app/lead_status_form.html'


class LeadStatusUpdateView(TemplateView):
    """Update lead status - placeholder."""
    template_name = 'settings_app/lead_status_form.html'


class LeadStatusDeleteView(TemplateView):
    """Delete lead status - placeholder."""
    template_name = 'settings_app/lead_status_confirm_delete.html'


class LeadSourceListView(TemplateView):
    """Lead source settings - placeholder."""
    template_name = 'settings_app/lead_source_list.html'


class LeadSourceCreateView(TemplateView):
    """Create lead source - placeholder."""
    template_name = 'settings_app/lead_source_form.html'


class LeadSourceUpdateView(TemplateView):
    """Update lead source - placeholder."""
    template_name = 'settings_app/lead_source_form.html'


class LeadSourceDeleteView(TemplateView):
    """Delete lead source - placeholder."""
    template_name = 'settings_app/lead_source_confirm_delete.html'


class OpportunityStageListView(TemplateView):
    """Opportunity stage settings - placeholder."""
    template_name = 'settings_app/opportunity_stage_list.html'


class OpportunityStageCreateView(TemplateView):
    """Create opportunity stage - placeholder."""
    template_name = 'settings_app/opportunity_stage_form.html'


class OpportunityStageUpdateView(TemplateView):
    """Update opportunity stage - placeholder."""
    template_name = 'settings_app/opportunity_stage_form.html'


class OpportunityStageDeleteView(TemplateView):
    """Delete opportunity stage - placeholder."""
    template_name = 'settings_app/opportunity_stage_confirm_delete.html'


class APIKeyListView(TemplateView):
    """API key list - placeholder."""
    template_name = 'settings_app/apikey_list.html'


class APIKeyCreateView(TemplateView):
    """Create API key - placeholder."""
    template_name = 'settings_app/apikey_form.html'


class APIKeyDeleteView(TemplateView):
    """Delete API key - placeholder."""
    template_name = 'settings_app/apikey_confirm_delete.html'


class WebhookListView(TemplateView):
    """Webhook list - placeholder."""
    template_name = 'settings_app/webhook_list.html'


class WebhookCreateView(TemplateView):
    """Create webhook - placeholder."""
    template_name = 'settings_app/webhook_form.html'


class WebhookUpdateView(TemplateView):
    """Update webhook - placeholder."""
    template_name = 'settings_app/webhook_form.html'


class WebhookDeleteView(TemplateView):
    """Delete webhook - placeholder."""
    template_name = 'settings_app/webhook_confirm_delete.html'


class ScoringRulesListView(TemplateView):
    """Scoring rules list - placeholder."""
    template_name = 'settings_app/scoring_rules_list.html'


class BehavioralScoringRuleCreateView(CreateView):
    """Create behavioral scoring rule."""
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'settings_app/behavioral_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class BehavioralScoringRuleUpdateView(UpdateView):
    """Update behavioral scoring rule."""
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'settings_app/behavioral_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class BehavioralScoringRuleDeleteView(DeleteView):
    """Delete behavioral scoring rule."""
    model = BehavioralScoringRule
    template_name = 'settings_app/behavioral_scoring_confirm_delete.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class DemographicScoringRuleCreateView(CreateView):
    """Create demographic scoring rule."""
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'settings_app/demographic_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class DemographicScoringRuleUpdateView(UpdateView):
    """Update demographic scoring rule."""
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'settings_app/demographic_scoring_form.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class DemographicScoringRuleDeleteView(DeleteView):
    """Delete demographic scoring rule."""
    model = DemographicScoringRule
    template_name = 'settings_app/demographic_scoring_confirm_delete.html'
    success_url = reverse_lazy('settings_app:scoring_rules_list')


class ScoreDecayConfigView(TemplateView):
    """Score decay config - placeholder."""
    template_name = 'settings_app/score_decay_config.html'


class SettingTypeListView(ListView):
    model = SettingType
    template_name = 'settings_app/setting_type_list.html'
    context_object_name = 'setting_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class SettingTypeCreateView(CreateView):
    model = SettingType
    form_class = SettingTypeForm
    template_name = 'settings_app/setting_type_form.html'
    success_url = reverse_lazy('settings_app:setting_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Setting type created successfully.')
        return super().form_valid(form)


class SettingTypeUpdateView(UpdateView):
    model = SettingType
    form_class = SettingTypeForm
    template_name = 'settings_app/setting_type_form.html'
    success_url = reverse_lazy('settings_app:setting_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Setting type updated successfully.')
        return super().form_valid(form)


class SettingTypeDeleteView(DeleteView):
    model = SettingType
    template_name = 'settings_app/setting_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:setting_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Setting type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ModelChoiceListView(ListView):
    model = ModelChoice
    template_name = 'settings_app/model_choice_list.html'
    context_object_name = 'model_choices'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ModelChoiceCreateView(CreateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'settings_app/model_choice_form.html'
    success_url = reverse_lazy('settings_app:model_choice_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Model choice created successfully.')
        return super().form_valid(form)


class ModelChoiceUpdateView(UpdateView):
    model = ModelChoice
    form_class = ModelChoiceForm
    template_name = 'settings_app/model_choice_form.html'
    success_url = reverse_lazy('settings_app:model_choice_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Model choice updated successfully.')
        return super().form_valid(form)


class ModelChoiceDeleteView(DeleteView):
    model = ModelChoice
    template_name = 'settings_app/model_choice_confirm_delete.html'
    success_url = reverse_lazy('settings_app:model_choice_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Model choice deleted successfully.')
        return super().delete(request, *args, **kwargs)


class FieldTypeListView(ListView):
    model = FieldType
    template_name = 'settings_app/field_type_list.html'
    context_object_name = 'field_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class FieldTypeCreateView(CreateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'settings_app/field_type_form.html'
    success_url = reverse_lazy('settings_app:field_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Field type created successfully.')
        return super().form_valid(form)


class FieldTypeUpdateView(UpdateView):
    model = FieldType
    form_class = FieldTypeForm
    template_name = 'settings_app/field_type_form.html'
    success_url = reverse_lazy('settings_app:field_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Field type updated successfully.')
        return super().form_valid(form)


class FieldTypeDeleteView(DeleteView):
    model = FieldType
    template_name = 'settings_app/field_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:field_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Field type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ModuleChoiceListView(ListView):
    model = ModuleChoice
    template_name = 'settings_app/module_choice_list.html'
    context_object_name = 'module_choices'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ModuleChoiceCreateView(CreateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'settings_app/module_choice_form.html'
    success_url = reverse_lazy('settings_app:module_choice_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Module choice created successfully.')
        return super().form_valid(form)


class ModuleChoiceUpdateView(UpdateView):
    model = ModuleChoice
    form_class = ModuleChoiceForm
    template_name = 'settings_app/module_choice_form.html'
    success_url = reverse_lazy('settings_app:module_choice_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Module choice updated successfully.')
        return super().form_valid(form)


class ModuleChoiceDeleteView(DeleteView):
    model = ModuleChoice
    template_name = 'settings_app/module_choice_confirm_delete.html'
    success_url = reverse_lazy('settings_app:module_choice_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Module choice deleted successfully.')
        return super().delete(request, *args, **kwargs)








class AssignmentRuleTypeListView(ListView):
    model = AssignmentRuleType
    template_name = 'settings_app/assignment_rule_type_list.html'
    context_object_name = 'assignment_rule_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class AssignmentRuleTypeCreateView(CreateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'settings_app/assignment_rule_type_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Assignment rule type created successfully.')
        return super().form_valid(form)


class AssignmentRuleTypeUpdateView(UpdateView):
    model = AssignmentRuleType
    form_class = AssignmentRuleTypeForm
    template_name = 'settings_app/assignment_rule_type_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Assignment rule type updated successfully.')
        return super().form_valid(form)


class AssignmentRuleTypeDeleteView(DeleteView):
    model = AssignmentRuleType
    template_name = 'settings_app/assignment_rule_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:assignment_rule_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PipelineTypeListView(ListView):
    model = PipelineType
    template_name = 'settings_app/pipeline_type_list.html'
    context_object_name = 'pipeline_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class PipelineTypeCreateView(CreateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'settings_app/pipeline_type_form.html'
    success_url = reverse_lazy('settings_app:pipeline_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Pipeline type created successfully.')
        return super().form_valid(form)


class PipelineTypeUpdateView(UpdateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'settings_app/pipeline_type_form.html'
    success_url = reverse_lazy('settings_app:pipeline_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Pipeline type updated successfully.')
        return super().form_valid(form)


class PipelineTypeDeleteView(DeleteView):
    model = PipelineType
    template_name = 'settings_app/pipeline_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:pipeline_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Pipeline type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class EmailProviderListView(ListView):
    model = EmailProvider
    template_name = 'settings_app/email_provider_list.html'
    context_object_name = 'email_providers'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class EmailProviderCreateView(CreateView):
    model = EmailProvider
    form_class = EmailProviderForm
    template_name = 'settings_app/email_provider_form.html'
    success_url = reverse_lazy('settings_app:email_provider_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Email provider created successfully.')
        return super().form_valid(form)


class EmailProviderUpdateView(UpdateView):
    model = EmailProvider
    form_class = EmailProviderForm
    template_name = 'settings_app/email_provider_form.html'
    success_url = reverse_lazy('settings_app:email_provider_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Email provider updated successfully.')
        return super().form_valid(form)


class EmailProviderDeleteView(DeleteView):
    model = EmailProvider
    template_name = 'settings_app/email_provider_confirm_delete.html'
    success_url = reverse_lazy('settings_app:email_provider_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email provider deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ActionTypeListView(ListView):
    model = ActionType
    template_name = 'settings_app/action_type_list.html'
    context_object_name = 'action_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class ActionTypeCreateView(CreateView):
    model = ActionType
    form_class = ActionTypeForm
    template_name = 'settings_app/action_type_form.html'
    success_url = reverse_lazy('settings_app:action_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Action type created successfully.')
        return super().form_valid(form)


class ActionTypeUpdateView(UpdateView):
    model = ActionType
    form_class = ActionTypeForm
    template_name = 'settings_app/action_type_form.html'
    success_url = reverse_lazy('settings_app:action_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Action type updated successfully.')
        return super().form_valid(form)


class ActionTypeDeleteView(DeleteView):
    model = ActionType
    template_name = 'settings_app/action_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:action_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Action type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class OperatorTypeListView(ListView):
    model = OperatorType
    template_name = 'settings_app/operator_type_list.html'
    context_object_name = 'operator_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class OperatorTypeCreateView(CreateView):
    model = OperatorType
    form_class = OperatorTypeForm
    template_name = 'settings_app/operator_type_form.html'
    success_url = reverse_lazy('settings_app:operator_type_list')
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Operator type created successfully.')
        return super().form_valid(form)


class OperatorTypeUpdateView(UpdateView):
    model = OperatorType
    form_class = OperatorTypeForm
    template_name = 'settings_app/operator_type_form.html'
    success_url = reverse_lazy('settings_app:operator_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Operator type updated successfully.')
        return super().form_valid(form)


class OperatorTypeDeleteView(DeleteView):
    model = OperatorType
    template_name = 'settings_app/operator_type_confirm_delete.html'
    success_url = reverse_lazy('settings_app:operator_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Operator type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class SettingListView(ListView):
    model = Setting
    template_name = 'settings_app/setting_list.html'
    context_object_name = 'settings'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('setting_type_ref', 'model_name_ref')


class SettingCreateView(CreateView):
    model = Setting
    form_class = SettingForm
    template_name = 'settings_app/setting_form.html'
    success_url = reverse_lazy('settings_app:setting_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Setting created successfully.')
        return super().form_valid(form)


class SettingUpdateView(UpdateView):
    model = Setting
    form_class = SettingForm
    template_name = 'settings_app/setting_form.html'
    success_url = reverse_lazy('settings_app:setting_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Setting updated successfully.')
        return super().form_valid(form)


class SettingDeleteView(DeleteView):
    model = Setting
    template_name = 'settings_app/setting_confirm_delete.html'
    success_url = reverse_lazy('settings_app:setting_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Setting deleted successfully.')
        return super().delete(request, *args, **kwargs)


class CustomFieldListView(ListView):
    model = CustomField
    template_name = 'settings_app/custom_field_list.html'
    context_object_name = 'custom_fields'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('model_name_ref', 'field_type_ref')


class CustomFieldCreateView(CreateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'settings_app/custom_field_form.html'
    success_url = reverse_lazy('settings_app:custom_field_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Custom field created successfully.')
        return super().form_valid(form)


class CustomFieldUpdateView(UpdateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'settings_app/custom_field_form.html'
    success_url = reverse_lazy('settings_app:custom_field_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Custom field updated successfully.')
        return super().form_valid(form)


class CustomFieldDeleteView(DeleteView):
    model = CustomField
    template_name = 'settings_app/custom_field_confirm_delete.html'
    success_url = reverse_lazy('settings_app:custom_field_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Custom field deleted successfully.')
        return super().delete(request, *args, **kwargs)


class ModuleLabelListView(ListView):
    model = ModuleLabel
    template_name = 'settings_app/module_label_list.html'
    context_object_name = 'module_labels'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('module_key_ref')


class ModuleLabelCreateView(CreateView):
    model = ModuleLabel
    form_class = ModuleLabelForm
    template_name = 'settings_app/module_label_form.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Module label created successfully.')
        return super().form_valid(form)


class ModuleLabelUpdateView(UpdateView):
    model = ModuleLabel
    form_class = ModuleLabelForm
    template_name = 'settings_app/module_label_form.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Module label updated successfully.')
        return super().form_valid(form)


class ModuleLabelDeleteView(DeleteView):
    model = ModuleLabel
    template_name = 'settings_app/module_label_confirm_delete.html'
    success_url = reverse_lazy('settings_app:module_label_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Module label deleted successfully.')
        return super().delete(request, *args, **kwargs)





class AssignmentRuleListView(ListView):
    model = AssignmentRule
    template_name = 'settings_app/assignment_rule_list.html'
    context_object_name = 'assignment_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('module_ref', 'rule_type_ref', 'assigned_to')


class AssignmentRuleCreateView(CreateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'settings_app/assignment_rule_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Assignment rule created successfully.')
        return super().form_valid(form)


class AssignmentRuleUpdateView(UpdateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'settings_app/assignment_rule_form.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Assignment rule updated successfully.')
        return super().form_valid(form)


class AssignmentRuleDeleteView(DeleteView):
    model = AssignmentRule
    template_name = 'settings_app/assignment_rule_confirm_delete.html'
    success_url = reverse_lazy('settings_app:assignment_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PipelineStageListView(ListView):
    model = PipelineStage
    template_name = 'settings_app/pipeline_stage_list.html'
    context_object_name = 'pipeline_stages'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('pipeline_type_ref')


class PipelineStageCreateView(CreateView):
    model = PipelineStage
    form_class = PipelineStageForm
    template_name = 'settings_app/pipeline_stage_form.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Pipeline stage created successfully.')
        return super().form_valid(form)


class PipelineStageUpdateView(UpdateView):
    model = PipelineStage
    form_class = PipelineStageForm
    template_name = 'settings_app/pipeline_stage_form.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Pipeline stage updated successfully.')
        return super().form_valid(form)


class PipelineStageDeleteView(DeleteView):
    model = PipelineStage
    template_name = 'settings_app/pipeline_stage_confirm_delete.html'
    success_url = reverse_lazy('settings_app:pipeline_stage_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Pipeline stage deleted successfully.')
        return super().delete(request, *args, **kwargs)


class EmailIntegrationListView(ListView):
    model = EmailIntegration
    template_name = 'settings_app/email_integration_list.html'
    context_object_name = 'email_integrations'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('user', 'provider_ref')


class EmailIntegrationCreateView(CreateView):
    model = EmailIntegration
    form_class = EmailIntegrationForm
    template_name = 'settings_app/email_integration_form.html'
    success_url = reverse_lazy('settings_app:email_integration_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Email integration created successfully.')
        return super().form_valid(form)


class EmailIntegrationUpdateView(UpdateView):
    model = EmailIntegration
    form_class = EmailIntegrationForm
    template_name = 'settings_app/email_integration_form.html'
    success_url = reverse_lazy('settings_app:email_integration_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Email integration updated successfully.')
        return super().form_valid(form)


class EmailIntegrationDeleteView(DeleteView):
    model = EmailIntegration
    template_name = 'settings_app/email_integration_confirm_delete.html'
    success_url = reverse_lazy('settings_app:email_integration_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Email integration deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BehavioralScoringRuleListView(ListView):
    model = BehavioralScoringRule
    template_name = 'settings_app/behavioral_scoring_rule_list.html'
    context_object_name = 'behavioral_scoring_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('action_type_ref', 'business_impact_ref')


class BehavioralScoringRuleCreateView(CreateView):
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'settings_app/behavioral_scoring_rule_form.html'
    success_url = reverse_lazy('settings_app:behavioral_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Behavioral scoring rule created successfully.')
        return super().form_valid(form)


class BehavioralScoringRuleUpdateView(UpdateView):
    model = BehavioralScoringRule
    form_class = BehavioralScoringRuleForm
    template_name = 'settings_app/behavioral_scoring_rule_form.html'
    success_url = reverse_lazy('settings_app:behavioral_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Behavioral scoring rule updated successfully.')
        return super().form_valid(form)


class BehavioralScoringRuleDeleteView(DeleteView):
    model = BehavioralScoringRule
    template_name = 'settings_app/behavioral_scoring_rule_confirm_delete.html'
    success_url = reverse_lazy('settings_app:behavioral_scoring_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Behavioral scoring rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


class DemographicScoringRuleListView(ListView):
    model = DemographicScoringRule
    template_name = 'settings_app/demographic_scoring_rule_list.html'
    context_object_name = 'demographic_scoring_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('operator_ref')


class DemographicScoringRuleCreateView(CreateView):
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'settings_app/demographic_scoring_rule_form.html'
    success_url = reverse_lazy('settings_app:demographic_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Demographic scoring rule created successfully.')
        return super().form_valid(form)


class DemographicScoringRuleUpdateView(UpdateView):
    model = DemographicScoringRule
    form_class = DemographicScoringRuleForm
    template_name = 'settings_app/demographic_scoring_rule_form.html'
    success_url = reverse_lazy('settings_app:demographic_scoring_rule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Demographic scoring rule updated successfully.')
        return super().form_valid(form)


class DemographicScoringRuleDeleteView(DeleteView):
    model = DemographicScoringRule
    template_name = 'settings_app/demographic_scoring_rule_confirm_delete.html'
    success_url = reverse_lazy('settings_app:demographic_scoring_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Demographic scoring rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_http_methods(["GET"])
def get_settings_dynamic_choices(request, model_name):
    """
    API endpoint to fetch dynamic choices for settings models
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Map model names to actual models
    model_map = {
        'settingtype': SettingType,
        'modelchoice': ModelChoice,
        'fieldtype': FieldType,
        'modulechoice': ModuleChoice,
        'teamrole': TeamRole,
        'territory': Territory,
        'assignmentruletype': AssignmentRuleType,
        'pipelinetype': PipelineType,
        'emailprovider': EmailProvider,
        'actiontype': ActionType,
        'operatortype': OperatorType,
    }
    
    model_class = model_map.get(model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        choices = model_class.objects.filter(tenant_id=tenant_id).values('id', 'name', 'label')
        return JsonResponse(list(choices), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
