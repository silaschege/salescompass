from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, ListView, View, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Tenant
from .data_preservation import TenantDataPreservation, TenantDataRestoration, TenantDataPreservationStrategy, TenantDataPreservationSchedule
from .automated_lifecycle import AutomatedTenantLifecycleRule, AutomatedTenantLifecycleEvent, TenantLifecycleWorkflow, TenantLifecycleWorkflowExecution, TenantSuspensionWorkflow, TenantTerminationWorkflow
from core.models import User


class TenantLifecycleDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view for tenant lifecycle management"""
    template_name = 'tenants/lifecycle_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenants'] = Tenant.objects.all()
        context['active_tenants'] = Tenant.objects.filter(is_active=True).count()
        context['suspended_tenants'] = Tenant.objects.filter(is_suspended=True).count()
        context['archived_tenants'] = Tenant.objects.filter(is_archived=True).count()
        context['automated_rules'] = AutomatedTenantLifecycleRule.objects.filter(is_active=True).count()
        context['recent_events'] = AutomatedTenantLifecycleEvent.objects.select_related('tenant', 'rule').order_by('-triggered_at')[:10]
        return context


class TenantStatusManagementView(LoginRequiredMixin, ListView):
    """View for managing tenant statuses"""
    template_name = 'tenants/status_management.html'
    model = Tenant
    context_object_name = 'tenants'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Tenant.objects.all()
        status_filter = self.request.GET.get('status')
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True, is_suspended=False, is_archived=False)
            elif status_filter == 'suspended':
                queryset = queryset.filter(is_suspended=True)
            elif status_filter == 'archived':
                queryset = queryset.filter(is_archived=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)
        return queryset


class TenantSuspensionWorkflowView(LoginRequiredMixin, CreateView):
    """View for initiating tenant suspension workflow"""
    template_name = 'tenants/suspension_workflow.html'
    model = TenantSuspensionWorkflow
    fields = ['tenant', 'suspension_reason']
    success_url = reverse_lazy('tenants:suspension-workflows')
    
    def form_valid(self, form):
        form.instance.initiated_by = self.request.user
        messages.success(self.request, f'Suspension workflow initiated for {form.instance.tenant.name}.')
        return super().form_valid(form)


class TenantTerminationWorkflowView(LoginRequiredMixin, CreateView):
    """View for initiating tenant termination workflow"""
    template_name = 'tenants/termination_workflow.html'
    model = TenantTerminationWorkflow
    fields = ['tenant', 'termination_reason', 'data_preservation_required']
    success_url = reverse_lazy('tenants:termination-workflows')
    
    def form_valid(self, form):
        form.instance.initiated_by = self.request.user
        messages.success(self.request, f'Termination workflow initiated for {form.instance.tenant.name}.')
        return super().form_valid(form)


class AutomatedLifecycleRulesView(LoginRequiredMixin, ListView):
    """View for managing automated lifecycle rules"""
    template_name = 'tenants/automated_lifecycle_rules.html'
    model = AutomatedTenantLifecycleRule
    context_object_name = 'rules'
    paginate_by = 20
    
    def get_queryset(self):
        return AutomatedTenantLifecycleRule.objects.select_related('created_by').all()


class CreateAutomatedLifecycleRuleView(LoginRequiredMixin, CreateView):
    """View for creating automated lifecycle rules"""
    template_name = 'tenants/create_automated_rule.html'
    model = AutomatedTenantLifecycleRule
    fields = ['name', 'description', 'condition_type', 'condition_field', 'condition_operator', 'condition_value', 'action_type', 'action_parameters', 'evaluation_frequency']
    success_url = reverse_lazy('tenants:automated-lifecycle-rules')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Automated lifecycle rule "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class TenantDataPreservationView(LoginRequiredMixin, ListView):
    """View for managing tenant data preservation"""
    template_name = 'tenants/data_preservation.html'
    model = TenantDataPreservation
    context_object_name = 'preservation_records'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantDataPreservation.objects.select_related('tenant', 'created_by').all()


class TenantDataRestorationView(LoginRequiredMixin, ListView):
    """View for managing tenant data restoration"""
    template_name = 'tenants/data_restoration.html'
    model = TenantDataRestoration
    context_object_name = 'restoration_records'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantDataRestoration.objects.select_related('tenant', 'preservation_record').all()


class TenantLifecycleWorkflowsView(LoginRequiredMixin, ListView):
    """View for managing tenant lifecycle workflows"""
    template_name = 'tenants/lifecycle_workflows.html'
    model = TenantLifecycleWorkflow
    context_object_name = 'workflows'
    paginate_by = 20
    
    def get_queryset(self):
        return TenantLifecycleWorkflow.objects.select_related('created_by').all()


class ApproveSuspensionWorkflowView(LoginRequiredMixin, View):
    """View for approving suspension workflows"""
    def post(self, request, workflow_id):
        workflow = get_object_or_404(TenantSuspensionWorkflow, id=workflow_id)
        notes = request.POST.get('approval_notes', '')
        
        workflow.approve(request.user, notes)
        messages.success(request, f'Suspension workflow for {workflow.tenant.name} approved.')
        
        return redirect('tenants:suspension-workflows')


class ApproveTerminationWorkflowView(LoginRequiredMixin, View):
    """View for approving termination workflows"""
    def post(self, request, workflow_id):
        workflow = get_object_or_404(TenantTerminationWorkflow, id=workflow_id)
        notes = request.POST.get('approval_notes', '')
        
        workflow.approve(request.user, notes)
        messages.success(request, f'Termination workflow for {workflow.tenant.name} approved.')
        
        return redirect('tenants:termination-workflows')


class TenantLifecycleEventLogView(LoginRequiredMixin, ListView):
    """View for viewing tenant lifecycle event logs"""
    template_name = 'tenants/lifecycle_event_log.html'
    model = AutomatedTenantLifecycleEvent
    context_object_name = 'events'
    paginate_by = 20
    
    def get_queryset(self):
        return AutomatedTenantLifecycleEvent.objects.select_related('tenant', 'rule', 'executed_by').order_by('-triggered_at')


@method_decorator(csrf_exempt, name='dispatch')
class ExecuteLifecycleRuleView(LoginRequiredMixin, View):
    """API view for executing lifecycle rules"""
    def post(self, request, rule_id):
        rule = get_object_or_404(AutomatedTenantLifecycleRule, id=rule_id)
        
        # In a real implementation, this would execute the rule logic
        # For now, we'll just log that the rule was executed
        tenants = Tenant.objects.all()
        executed_count = 0
        
        for tenant in tenants:
            # Evaluate the rule condition for each tenant
            # This is a simplified version - in a real implementation, 
            # you would have more complex logic to evaluate the condition
            condition_met = self.evaluate_condition(tenant, rule)
            
            if condition_met:
                # Execute the action for this tenant
                self.execute_action(tenant, rule)
                
                # Log the event
                AutomatedTenantLifecycleEvent.objects.create(
                    rule=rule,
                    tenant=tenant,
                    event_type='action_taken',
                    status='success',
                    details=f'Action {rule.action_type} taken for tenant {tenant.name}',
                    executed_by=request.user
                )
                executed_count += 1
        
        # Update the rule's last evaluation time
        rule.last_evaluated = timezone.now()
        rule.next_evaluation = self.calculate_next_evaluation(rule)
        rule.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Rule {rule.name} executed for {executed_count} tenants',
            'executed_count': executed_count
        })
    
    def evaluate_condition(self, tenant, rule):
        """Evaluate if the condition is met for a tenant"""
        # This is a simplified condition evaluation
        # In a real implementation, you would have more complex logic
        if rule.condition_type == 'usage_based':
            if rule.condition_field == 'storage_used' and rule.condition_operator == 'greater_than':
                # This would check the actual storage usage
                return False  # Placeholder
        elif rule.condition_type == 'billing_based':
            if rule.condition_field == 'subscription_status' and rule.condition_operator == 'equals':
                return getattr(tenant, rule.condition_field) == rule.condition_value
        elif rule.condition_type == 'time_based':
            if rule.condition_field == 'trial_end_date' and rule.condition_operator == 'less_than':
                return tenant.trial_end_date and tenant.trial_end_date < timezone.now()
        
        return False
    
    def execute_action(self, tenant, rule):
        """Execute the action for a tenant"""
        if rule.action_type == 'suspend':
            tenant.suspend(reason=f'Automated suspension by rule: {rule.name}', triggered_by=self.request.user)
        elif rule.action_type == 'terminate':
            tenant.soft_delete(triggered_by=self.request.user)
        elif rule.action_type == 'archive':
            tenant.archive(triggered_by=self.request.user)
        elif rule.action_type == 'reactivate':
            tenant.reactivate(triggered_by=self.request.user)
        # Add more actions as needed
    
    def calculate_next_evaluation(self, rule):
        """Calculate the next evaluation time based on frequency"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        if rule.evaluation_frequency == 'hourly':
            return now + timedelta(hours=1)
        elif rule.evaluation_frequency == 'daily':
            return now + timedelta(days=1)
        elif rule.evaluation_frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif rule.evaluation_frequency == 'monthly':
            return now + timedelta(days=30)
        
        return now + timedelta(days=1)  # Default to daily


class TenantRestorationView(LoginRequiredMixin, View):
    """View for initiating tenant data restoration"""
    def get(self, request, preservation_id):
        preservation = get_object_or_404(TenantDataPreservation, id=preservation_id)
        return render(request, 'tenants/initiate_restoration.html', {'preservation': preservation})
    
    def post(self, request, preservation_id):
        preservation = get_object_or_404(TenantDataPreservation, id=preservation_id)
        
        # Create a restoration record
        restoration = TenantDataRestoration.objects.create(
            tenant=preservation.tenant,
            preservation_record=preservation,
            description=f'Restoration from {preservation.preservation_type} at {preservation.preservation_date}',
            initiated_by=request.user
        )
        
        # In a real implementation, this would trigger the actual restoration process
        # For now, we'll just update the status
        restoration.status = 'completed'
        restoration.completed_at = timezone.now()
        restoration.completed_by = request.user
        restoration.total_records = 100  # Placeholder
        restoration.restored_records = 100  # Placeholder
        restoration.progress_percentage = 10.0
        restoration.save()
        
        messages.success(request, f'Data restoration completed for {preservation.tenant.name}.')
        return redirect('tenants:data-restoration')
