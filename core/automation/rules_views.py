from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import AutomationRule

class AutomationRuleListView(LoginRequiredMixin, ListView):
    model = AutomationRule
    template_name = 'automation/rule_list.html'
    context_object_name = 'rules'

    def get_queryset(self):
        # Filter by tenant
        return AutomationRule.objects.filter(tenant=self.request.user.tenant)

class AutomationRuleCreateView(LoginRequiredMixin, CreateView):
    model = AutomationRule
    template_name = 'automation/rule_form.html'
    fields = ['automation_rule_name', 'automation_rule_description', 'trigger_type', 'conditions', 'actions', 'automation_rule_is_active']
    success_url = reverse_lazy('automation:rule_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant = self.request.user.tenant
        messages.success(self.request, "Business Rule created successfully.")
        return super().form_valid(form)

class AutomationRuleUpdateView(LoginRequiredMixin, UpdateView):
    model = AutomationRule
    template_name = 'automation/rule_form.html'
    fields = ['automation_rule_name', 'automation_rule_description', 'trigger_type', 'conditions', 'actions', 'automation_rule_is_active']
    success_url = reverse_lazy('automation:rule_list')

    def get_queryset(self):
        return AutomationRule.objects.filter(tenant=self.request.user.tenant)
    
    def form_valid(self, form):
        messages.success(self.request, "Business Rule updated successfully.")
        return super().form_valid(form)

class AutomationRuleDeleteView(LoginRequiredMixin, DeleteView):
    model = AutomationRule
    template_name = 'automation/rule_confirm_delete.html'
    success_url = reverse_lazy('automation:rule_list')

    def get_queryset(self):
        return AutomationRule.objects.filter(tenant=self.request.user.tenant)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Business Rule deleted successfully.")
        return super().delete(request, *args, **kwargs)
