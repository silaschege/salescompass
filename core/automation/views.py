from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.views import (
    SalesCompassListView, SalesCompassDetailView, SalesCompassCreateView,
    SalesCompassUpdateView, SalesCompassDeleteView, TenantAwareViewMixin
)
from core.permissions import PermissionRequiredMixin, require_permission
from .models import Automation, AutomationCondition, AutomationAction, Workflow, WorkflowTemplate,WorkflowAction,WorkflowTrigger,WorkflowExecution,WebhookDeliveryLog,WebhookEndpoint, WorkflowApproval, WorkflowVersion, CustomCodeSnippet, CustomCodeExecutionLog
from .forms import AutomationForm, AutomationConditionForm, AutomationActionForm, CustomCodeSnippetForm
from .utils import get_available_triggers
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import AutomationExecutionLog, WorkflowExecution
from .utils import emit_event, execute_automation
from django.utils import timezone
class WorkflowListView(SalesCompassListView):
    model = Workflow
    template_name = 'automation/list.html'
    context_object_name = 'workflows'
    
    def get_queryset(self):
        # SalesCompassListView handles tenant filtering automatically if needed, 
        # but here we might want specific logic or just rely on default
        return super().get_queryset()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflows = self.get_queryset()
        context['total_workflows'] = workflows.count()
        context['active_workflows'] = workflows.filter(workflow_is_active=True).count()
        context['inactive_workflows'] = workflows.filter(workflow_is_active=False).count()
        return context

class WorkflowDetailView(SalesCompassDetailView):
    model = Workflow
    template_name = 'automation/detail.html'

class WorkflowUpdateView(SalesCompassUpdateView):
    model = Workflow
    fields = ['workflow_name', 'workflow_description', 'workflow_trigger_type', 'workflow_is_active', 'workflow_builder_data']
    template_name = 'automation/form.html'
    success_url = '/automation/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context

class WorkflowCreateView(SalesCompassCreateView):
    model = Workflow
    fields = ['workflow_name', 'workflow_description', 'workflow_trigger_type', 'workflow_is_active', 'workflow_builder_data']
    template_name = 'automation/form.html'
    success_url = '/automation/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context

class WorkflowDeleteView(SalesCompassDeleteView):
    model = Workflow
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    
    def delete(self, request, *args, **kwargs):
        workflow = self.get_object()
        # Check if workflow is system workflow if such a field exists
        # if hasattr(workflow, 'is_system') and workflow.is_system:
        #     messages.error(request, "System workflows cannot be deleted.")
        #     return redirect('automation:list')
        messages.success(request, f"Workflow '{workflow.workflow_name}' deleted.")
        return super().delete(request, *args, **kwargs)

# Standard views for the older Automation model# Standard views for the older Automation model
class AutomationListView(SalesCompassListView):
    model = Automation
    template_name = 'automation/list.html'
    context_object_name = 'automations'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        automations = self.get_queryset()
        context['total_automations'] = automations.count()
        context['active_automations'] = automations.filter(automation_is_active=True).count()
        context['inactive_automations'] = automations.filter(automation_is_active=False).count()
        
        # Also include workflows for the combined list view
        from .models import Workflow
        workflows = Workflow.objects.all()
        context['workflows'] = workflows
        context['total_workflows'] = workflows.count()
        context['active_workflows'] = workflows.filter(workflow_is_active=True).count()
        return context

class AutomationDetailView(SalesCompassDetailView):
    model = Automation
    template_name = 'automation/detail.html'

class AutomationUpdateView(SalesCompassUpdateView):
    model = Automation
    fields = ['automation_name', 'automation_description', 'automation_is_active', 'trigger_type', 'trigger_config']
    template_name = 'automation/form.html'
    success_url = '/automation/'

class AutomationCreateView(SalesCompassCreateView):
    model = Automation
    fields = ['automation_name', 'automation_description', 'automation_is_active', 'trigger_type', 'trigger_config']
    template_name = 'automation/form.html'
    success_url = '/automation/'

class AutomationDeleteView(SalesCompassDeleteView):
    model = Automation
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'

class TriggerAutomationView(TenantAwareViewMixin, View):
    """API endpoint to trigger automations from other modules."""
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            data = json.loads(request.body)
            trigger_type = data.get('trigger_type')
            payload = data.get('payload', {})
            
            if not trigger_type:
                return JsonResponse({'error': 'trigger_type is required'}, status=400)
            
            # Add tenant_id to payload if not present
            if 'tenant_id' not in payload and hasattr(request, 'tenant'):
                payload['tenant_id'] = request.tenant.id
            elif 'tenant_id' not in payload and hasattr(request.user, 'tenant_id'):
                 payload['tenant_id'] = request.user.tenant_id
            
            # Emit the event (this will trigger automations)
            emit_event(trigger_type, payload)
            
            return JsonResponse({'success': True, 'message': f'Event {trigger_type} triggered'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class ExecuteAutomationView(TenantAwareViewMixin, View):
    """API endpoint to execute a specific automation."""
    
    def post(self, request, automation_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        
        try:
            automation = get_object_or_404(Automation, id=automation_id)
            
            # Permission check
            if not request.user.has_perm('automation:write'):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            data = json.loads(request.body)
            payload = data.get('payload', {})
            
            success = execute_automation(automation, payload, request.user)
            
            if success:
                return JsonResponse({'success': True, 'message': 'Automation executed successfully'})
            else:
                return JsonResponse({'error': 'Automation execution failed'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=40)

class WorkflowExecutionListView(SalesCompassListView):
    """List all workflow execution logs."""
    model = WorkflowExecution
    template_name = 'automation/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')

class AutomationLogListView(SalesCompassListView):
    """List all automation execution logs."""
    model = AutomationExecutionLog
    template_name = 'automation/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('automation', 'executed_by')

class WorkflowExecutionDetailView(SalesCompassDetailView):
    """Detail view for workflow execution logs."""
    model = WorkflowExecution
    template_name = 'automation/log_detail.html'

class AutomationLogDetailView(SalesCompassDetailView):
    """Detail view for automation execution logs."""
    model = AutomationExecutionLog
    template_name = 'automation/log_detail.html'

class WebhookDeliveryLogListView(SalesCompassListView):
    """List all webhook delivery logs."""
    model = WebhookDeliveryLog
    template_name = 'automation/webhook_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('webhook_endpoint')

class WebhookDeliveryLogDetailView(SalesCompassDetailView):
    """Detail view for webhook delivery logs."""
    model = WebhookDeliveryLog
    template_name = 'automation/webhook_log_detail.html'
    context_object_name = 'log'

class WorkflowApprovalListView(SalesCompassListView):
    """List all pending workflow approval requests."""
    model = WorkflowApproval
    template_name = 'automation/approval_list.html'
    context_object_name = 'approvals'

    def get_queryset(self):
        return WorkflowApproval.objects.filter(
            tenant_id=self.request.user.tenant_id,
            approval_status='pending'
        ).select_related('workflow_execution', 'workflow_execution__workflow', 'workflow_action')

@login_required
def respond_to_workflow_approval(request, approval_id):
    """Handle approval or rejection of a workflow step."""
    from .models import WorkflowApproval
    from .engine import WorkflowEngine
    
    approval = get_object_or_404(WorkflowApproval, id=approval_id, tenant_id=request.user.tenant_id)
    
    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        comments = request.POST.get('comments', '')
        
        if action == 'approve':
            approval.approval_status = 'approved'
            approval.approval_responded_by = request.user
            approval.approval_responded_at = timezone.now()
            approval.approval_comments = comments
            approval.save()
            
            # Resume the workflow execution
            engine = WorkflowEngine()
            engine.resume_workflow(approval.workflow_execution.id)
            
            messages.success(request, "Workflow execution approved and resumed.")
            
        elif action == 'reject':
            approval.approval_status = 'rejected'
            approval.approval_responded_by = request.user
            approval.approval_responded_at = timezone.now()
            approval.approval_comments = comments
            approval.save()
            
            # Update execution status to failed
            execution = approval.workflow_execution
            execution.workflow_execution_status = 'failed'
            execution.workflow_execution_error_message = f"Rejected by {request.user.email}: {comments}"
            execution.save()
            
            messages.warning(request, "Workflow execution rejected.")
            
        return redirect('automation:approval_list')
        
    return render(request, 'automation/approval_response.html', {'approval': approval})

class SystemAutomationListView(SalesCompassListView):
    """List system automations (cannot be deleted)."""
    model = Automation
    template_name = 'automation/system_list.html'
    context_object_name = 'automations'

    def get_queryset(self):
        return Automation.objects.filter(is_system=True)

def import_automation_view(request):
    """Import automation rules from JSON file."""
    if request.method == 'POST' and request.user.has_perm('automation:write'):
        # Handle file upload and import logic here
        messages.success(request, "Automation rules imported successfully!")
        return redirect('automation:list')
    return render(request, 'automation/import.html')

def export_automation_view(request):
    """Export automation rules as JSON."""
    if request.user.has_perm('automation:read'):
        # Generate JSON export
        from django.http import JsonResponse
        # ... export logic ...
        return JsonResponse({'message': 'Export functionality placeholder'})
    return redirect('automation:log_list')

# In your views.py, update the form handling

class AutomationConditionCreateView(SalesCompassCreateView):
    model = AutomationCondition
    form_class = AutomationConditionForm
    template_name = 'automation/condition_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        automation_id = self.kwargs.get('automation_id')
        if automation_id:
            kwargs['automation'] = get_object_or_404(Automation, id=automation_id)
        return kwargs

    def form_valid(self, form):
        automation_id = self.kwargs.get('automation_id')
        form.instance.automation_id = automation_id
        return super().form_valid(form)

class AutomationActionCreateView(SalesCompassCreateView):
    model = AutomationAction
    form_class = AutomationActionForm
    template_name = 'automation/action_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        automation_id = self.kwargs.get('automation_id')
        if automation_id:
            kwargs['automation'] = get_object_or_404(Automation, id=automation_id)
        return kwargs

    def form_valid(self, form):
        automation_id = self.kwargs.get('automation_id')
        form.instance.automation_id = automation_id
        return super().form_valid(form)

@require_permission('automation:write')
def workflow_builder(request, workflow_id=None):
    """Visual workflow builder interface."""
    from .models import Workflow, WorkflowTemplate
    from .module_config import MODULE_CONFIG
    
    context = {
        'page_title': 'Workflow Builder',
        'templates': WorkflowTemplate.objects.filter(workflow_template_is_active=True),
        'module_config': MODULE_CONFIG,
        'module_config_json': json.dumps(MODULE_CONFIG) if MODULE_CONFIG else '{}'
    }
    
    if workflow_id:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        context['workflow'] = workflow
        context['workflow_id'] = workflow_id
        if hasattr(workflow, 'workflow_builder_data') and workflow.workflow_builder_data:
            context['workflow_data'] = json.dumps(workflow.workflow_builder_data)
            
    template_id = request.GET.get('template_id')
    if template_id and not workflow_id:
        template = get_object_or_404(WorkflowTemplate, id=template_id)
        context['workflow_data'] = json.dumps(template.workflow_template_builder_data)
        context['template_name'] = template.workflow_template_name
    
    return render(request, 'automation/workflow_builder.html', context)

@csrf_exempt
@require_permission('automation:write')
def save_workflow(request):
    """Save workflow from visual builder."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        from .models import Workflow
        
        data = json.loads(request.body)
        workflow_name = data.get('name')
        workflow_data = data.get('workflow_data', {})
        workflow_id = data.get('id')
        
        if not workflow_name:
            return JsonResponse({'error': 'Workflow name is required'}, status=400)
        
        # Handle update vs create
        if workflow_id:
            workflow = get_object_or_404(Workflow, id=workflow_id)
            workflow.workflow_name = workflow_name
            workflow.workflow_builder_data = workflow_data
        else:
            # Extract trigger type from workflow data
            trigger_type = 'default.trigger'
            if isinstance(workflow_data, dict) and 'steps' in workflow_data:
                # Form-based workflow
                steps = workflow_data.get('steps', [])
                for step in steps:
                    if step.get('type') == 'trigger' and 'event' in step:
                        trigger_type = step['event']
                        break
            else:
                # Visual workflow (drawflow format)
                drawflow = workflow_data.get('drawflow', {})
                home = drawflow.get('Home', {})
                nodes = home.get('data', {})
                for node_id, node in nodes.items():
                    if node.get('name') == 'trigger' and 'data' in node and 'event_type' in node['data']:
                        trigger_type = node['data']['event_type']
                        break
            
            workflow = Workflow(
                workflow_name=workflow_name,
                workflow_trigger_type=trigger_type,
                workflow_is_active=True,
                tenant_id=request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
                created_by=request.user if request.user.is_authenticated else None,
                workflow_builder_data=workflow_data
            )
        
        workflow.save()
        
        # Sync related models (Trigger, Actions, Branches) from JSON data
        from .utils import sync_workflow_from_builder_data
        sync_workflow_from_builder_data(workflow)
        
        return JsonResponse({
            'success': True,
            'workflow_id': workflow.id,
            'message': 'Workflow saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def load_workflow(request, workflow_id):
    """Load workflow data for visual builder."""
    from .models import Workflow
    
    try:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        
        # Convert workflow to drawflow format
        workflow_data = {
            'name': workflow.workflow_name,
            'trigger_type': workflow.workflow_trigger_type,
            # Add drawflow data here
        }
        
        return JsonResponse({
            'success': True,
            'workflow': workflow_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Additional views for Workflow models
class WorkflowActionCreateView(SalesCompassCreateView):
    model = WorkflowAction
    fields = ['workflow_action_type', 'workflow_action_parameters', 'workflow_action_order', 'workflow_action_is_active']
    template_name = 'automation/workflow_action_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        workflow_id = self.kwargs.get('workflow_id')
        if workflow_id:
            workflow = get_object_or_404(Workflow, id=workflow_id)
            kwargs['initial'] = {'workflow': workflow}
        return kwargs

    def form_valid(self, form):
        workflow_id = self.kwargs.get('workflow_id')
        form.instance.workflow_id = workflow_id
        return super().form_valid(form)



class WorkflowTriggerCreateView(SalesCompassCreateView):
    model = WorkflowTrigger
    fields = ['workflow_trigger_event', 'workflow_trigger_conditions', 'workflow_trigger_is_active']
    template_name = 'automation/workflow_trigger_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        workflow_id = self.kwargs.get('workflow_id')
        if workflow_id:
            workflow = get_object_or_404(Workflow, id=workflow_id)
            kwargs['initial'] = {'workflow': workflow}
        return kwargs

    def form_valid(self, form):
        workflow_id = self.kwargs.get('workflow_id')
        form.instance.workflow_id = workflow_id
        return super().form_valid(form)



# Additional views for Workflow models

class WorkflowActionListView(SalesCompassListView):
    model = WorkflowAction
    template_name = 'automation/workflow_action_list.html'
    context_object_name = 'workflow_actions'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')

class WorkflowActionDetailView(SalesCompassDetailView):
    model = WorkflowAction
    template_name = 'automation/workflow_action_detail.html'

class WorkflowActionUpdateView(SalesCompassUpdateView):
    model = WorkflowAction
    fields = ['workflow_action_type', 'workflow_action_parameters', 'workflow_action_order', 'workflow_action_is_active']
    template_name = 'automation/workflow_action_form.html'
    success_url = '/automation/workflow-actions/'

class WorkflowActionDeleteView(SalesCompassDeleteView):
    model = WorkflowAction
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-actions/'

class WorkflowExecutionListView(SalesCompassListView):
    model = WorkflowExecution
    template_name = 'automation/workflow_execution_list.html'
    context_object_name = 'workflow_executions'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')

class WorkflowExecutionDetailView(SalesCompassDetailView):
    model = WorkflowExecution
    template_name = 'automation/workflow_execution_detail.html'

class WorkflowExecutionUpdateView(SalesCompassUpdateView):
    model = WorkflowExecution
    fields = ['workflow_execution_status', 'workflow_execution_error_message', 'workflow_execution_completed_at']
    template_name = 'automation/workflow_execution_form.html'
    success_url = '/automation/workflow-executions/'

class WorkflowTriggerListView(SalesCompassListView):
    model = WorkflowTrigger
    template_name = 'automation/workflow_trigger_list.html'
    context_object_name = 'workflow_triggers'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')

class WorkflowTriggerDetailView(SalesCompassDetailView):
    model = WorkflowTrigger
    template_name = 'automation/workflow_trigger_detail.html'

class WorkflowTriggerUpdateView(SalesCompassUpdateView):
    model = WorkflowTrigger
    fields = ['workflow_trigger_event', 'workflow_trigger_conditions', 'workflow_trigger_is_active']
    template_name = 'automation/workflow_trigger_form.html'
    success_url = '/automation/workflow-triggers/'

class WorkflowTriggerDeleteView(SalesCompassDeleteView):
    model = WorkflowTrigger
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-triggers/'

class WorkflowTemplateListView(SalesCompassListView):
    model = WorkflowTemplate
    template_name = 'automation/workflow_template_list.html'
    context_object_name = 'workflow_templates'

class WorkflowTemplateDetailView(SalesCompassDetailView):
    model = WorkflowTemplate
    template_name = 'automation/workflow_template_detail.html'

class WorkflowTemplateUpdateView(SalesCompassUpdateView):
    model = WorkflowTemplate
    fields = ['workflow_template_name', 'workflow_template_description', 'workflow_template_trigger_type', 'workflow_template_builder_data', 'workflow_template_is_active']
    template_name = 'automation/workflow_template_form.html'
    success_url = '/automation/workflow-templates/'

class WorkflowTemplateDeleteView(SalesCompassDeleteView):
    model = WorkflowTemplate
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-templates/'

# ============================================================================
# Analytics Dashboard Views
# ============================================================================

class WorkflowAnalyticsDashboardView(TenantAwareViewMixin, View):
    """Main analytics dashboard view."""
    template_name = 'automation/analytics_dashboard.html'
    
    def get(self, request):
        from .analytics import analytics_service
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        tenant_id = getattr(request, 'tenant', None)
        tenant_id = tenant_id.id if tenant_id else None
        
        # Get date range from query params
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        context = {
            'page_title': 'Workflow Analytics',
            'tenant_analytics': analytics_service.get_tenant_analytics(
                tenant_id=tenant_id,
                start_date=start_date,
            ),
            'execution_trends': analytics_service.get_execution_trends(
                tenant_id=tenant_id,
                days=days,
            ),
            'action_stats': analytics_service.get_action_type_stats(
                tenant_id=tenant_id,
                days=days,
            ),
            'days': days,
        }
        
        return render(request, self.template_name, context)

class WorkflowAnalyticsAPIView(TenantAwareViewMixin, View):
    """API endpoint for analytics data (JSON)."""
    
    def get(self, request):
        from .analytics import analytics_service
        from datetime import timedelta
        from django.utils import timezone
        
        tenant_id = getattr(request, 'tenant', None)
        tenant_id = tenant_id.id if tenant_id else None
        workflow_id = request.GET.get('workflow_id')
        days = int(request.GET.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        
        if workflow_id:
            data = analytics_service.get_workflow_metrics(
                workflow_id=int(workflow_id),
                start_date=start_date,
            )
        else:
            data = {
                'tenant_analytics': analytics_service.get_tenant_analytics(
                    tenant_id=tenant_id,
                    start_date=start_date,
                ),
                'trends': analytics_service.get_execution_trends(
                    tenant_id=tenant_id,
                    days=days,
                ),
            }
        
        return JsonResponse(data)

# ============================================================================
# Execution Replay Views
# ============================================================================

class ReplayWorkflowExecutionView(TenantAwareViewMixin, View):
    """Replay a workflow execution."""
    
    def post(self, request, pk):
        from .models import WorkflowExecution
        from .engine import WorkflowEngine
        from django.utils import timezone
        
        original = get_object_or_404(WorkflowExecution, pk=pk)
        
        # Create a new execution as a replay
        replay_execution = WorkflowExecution.objects.create(
            workflow=original.workflow,
            workflow_execution_trigger_payload=original.workflow_execution_trigger_payload,
            workflow_execution_status='pending',
            is_replay=True,
            original_execution=original,
            tenant_id=original.tenant_id,
        )
        
        # Execute the workflow
        engine = WorkflowEngine()
        context = {
            'payload': original.workflow_execution_trigger_payload,
            'tenant_id': original.tenant_id,
            'is_replay': True,
        }
        
        try:
            success = engine.execute_workflow(original.workflow.id, context)
            
            if success:
                messages.success(request, f"Workflow replayed successfully. New execution ID: {replay_execution.id}")
            else:
                messages.warning(request, "Workflow replay completed with issues. Check execution log for details.")
                
        except Exception as e:
            messages.error(request, f"Replay failed: {str(e)}")
        
        return redirect('automation:workflow_execution_detail', pk=replay_execution.id)

# ============================================================================
# Version History Views
# ============================================================================

class WorkflowVersionListView(SalesCompassListView):
    """List all versions of a workflow."""
    model = WorkflowVersion
    template_name = 'automation/version_history.html'
    context_object_name = 'versions'
    
    def get_queryset(self):
        from .models import WorkflowVersion
        workflow_id = self.kwargs.get('workflow_id')
        return WorkflowVersion.objects.filter(workflow_id=workflow_id).select_related('created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = get_object_or_404(Workflow, pk=self.kwargs.get('workflow_id'))
        return context

class WorkflowRollbackView(TenantAwareViewMixin, View):
    """Rollback workflow to a previous version."""
    required_permission = 'automation:write'
    
    def post(self, request, workflow_id, version_id):
        from .models import WorkflowVersion
        
        workflow = get_object_or_404(Workflow, pk=workflow_id)
        version = get_object_or_404(WorkflowVersion, pk=version_id, workflow=workflow)
        
        # Create a new version before rollback (for safety)
        current_version_num = WorkflowVersion.objects.filter(workflow=workflow).count() + 1
        WorkflowVersion.objects.create(
            workflow=workflow,
            version_number=current_version_num,
            workflow_data_snapshot=workflow.workflow_builder_data,
            change_summary=f"Auto-saved before rollback to version {version.version_number}",
            created_by=request.user,
            tenant_id=workflow.tenant_id,
        )
        
        # Apply the rollback
        workflow.workflow_builder_data = version.workflow_data_snapshot
        workflow.save()
        
        # Sync related models
        from .utils import sync_workflow_from_builder_data
        sync_workflow_from_builder_data(workflow)
        
        messages.success(request, f"Workflow rolled back to version {version.version_number}")
        return redirect('automation:workflow_detail', pk=workflow_id)


# ============================================================================
# Custom Code Snippet Views
# ============================================================================

class CustomCodeSnippetListView(SalesCompassListView):
    """List all custom code snippets."""
    model = CustomCodeSnippet
    template_name = 'automation/custom_code_snippet_list.html'
    context_object_name = 'snippets'

    def get_queryset(self):
        return super().get_queryset().select_related('created_by')

class CustomCodeSnippetDetailView(SalesCompassDetailView):
    """View a custom code snippet."""
    model = CustomCodeSnippet
    template_name = 'automation/custom_code_snippet_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['execution_logs'] = self.object.execution_logs.all()[:10]
        return context

class CustomCodeSnippetCreateView(SalesCompassCreateView):
    """Create a new custom code snippet."""
    model = CustomCodeSnippet
    form_class = CustomCodeSnippetForm
    template_name = 'automation/custom_code_snippet_form.html'
    success_url = '/automation/custom-code-snippets/'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Custom code snippet created successfully.")
        return super().form_valid(form)

class CustomCodeSnippetUpdateView(SalesCompassUpdateView):
    """Update a custom code snippet."""
    model = CustomCodeSnippet
    form_class = CustomCodeSnippetForm
    template_name = 'automation/custom_code_snippet_form.html'
    success_url = '/automation/custom-code-snippets/'

    def form_valid(self, form):
        messages.success(self.request, "Custom code snippet updated successfully.")
        return super().form_valid(form)

class CustomCodeSnippetDeleteView(SalesCompassDeleteView):
    """Delete a custom code snippet."""
    model = CustomCodeSnippet
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/custom-code-snippets/'

class CustomCodeExecutionLogListView(SalesCompassListView):
    """List custom code execution logs."""
    model = CustomCodeExecutionLog
    template_name = 'automation/custom_code_execution_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('custom_code_snippet', 'workflow_execution')
