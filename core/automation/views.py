from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from core.permissions import PermissionRequiredMixin, require_permission
from .models import Automation, AutomationCondition, AutomationAction, Workflow, WorkflowTemplate,WorkflowAction,WorkflowTrigger,WorkflowExecution,WebhookDeliveryLog,WebhookEndpoint
from .forms import AutomationForm, AutomationConditionForm, AutomationActionForm
from .utils import get_available_triggers
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import AutomationExecutionLog, WorkflowExecution
from .utils import emit_event, execute_automation

class WorkflowListView(PermissionRequiredMixin, ListView):
    model = Workflow
    template_name = 'automation/list.html'
    context_object_name = 'workflows'
    required_permission = 'automation:read'
    
    def get_queryset(self):
        # Ensure we're getting all workflows, or apply specific filters
        return Workflow.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for workflow in context['workflows']:
            print(f"Workflow ID: {workflow.pk}")
        print(f"Workflows count: {context['workflows'].count()}")  # Debug line
        return context

class WorkflowDetailView(PermissionRequiredMixin, DetailView):
    model = Workflow
    template_name = 'automation/detail.html'
    required_permission = 'automation:read'

class WorkflowUpdateView(PermissionRequiredMixin, UpdateView):
    model = Workflow
    fields = ['workflow_name', 'workflow_description', 'workflow_trigger_type', 'workflow_is_active', 'workflow_builder_data']
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context

class WorkflowCreateView(PermissionRequiredMixin, CreateView):
    model = Workflow
    fields = ['workflow_name', 'workflow_description', 'workflow_trigger_type', 'workflow_is_active', 'workflow_builder_data']
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context

class WorkflowDeleteView(PermissionRequiredMixin, DeleteView):
    model = Workflow
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    required_permission = 'automation:delete'
    
    def delete(self, request, *args, **kwargs):
        workflow = self.get_object()
        # Check if workflow is system workflow if such a field exists
        # if hasattr(workflow, 'is_system') and workflow.is_system:
        #     messages.error(request, "System workflows cannot be deleted.")
        #     return redirect('automation:list')
        messages.success(request, f"Workflow '{workflow.workflow_name}' deleted.")
        return super().delete(request, *args, **kwargs)

# Standard views for the older Automation model
class AutomationListView(PermissionRequiredMixin, ListView):
    model = Automation
    template_name = 'automation/list.html'
    context_object_name = 'automations'
    required_permission = 'automation:read'

class AutomationDetailView(PermissionRequiredMixin, DetailView):
    model = Automation
    template_name = 'automation/detail.html'
    required_permission = 'automation:read'

class AutomationUpdateView(PermissionRequiredMixin, UpdateView):
    model = Automation
    fields = ['automation_name', 'automation_description', 'automation_is_active', 'trigger_type', 'trigger_config']
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

class AutomationCreateView(PermissionRequiredMixin, CreateView):
    model = Automation
    fields = ['automation_name', 'automation_description', 'automation_is_active', 'trigger_type', 'trigger_config']
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

class AutomationDeleteView(PermissionRequiredMixin, DeleteView):
    model = Automation
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    required_permission = 'automation:delete'

class TriggerAutomationView(View):
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
            if 'tenant_id' not in payload and hasattr(request.user, 'tenant_id'):
                payload['tenant_id'] = request.user.tenant_id
            
            # Emit the event (this will trigger automations)
            emit_event(trigger_type, payload)
            
            return JsonResponse({'success': True, 'message': f'Event {trigger_type} triggered'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class ExecuteAutomationView(View):
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

class WorkflowExecutionListView(PermissionRequiredMixin, ListView):
    """List all workflow execution logs."""
    model = WorkflowExecution
    template_name = 'automation/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')

class AutomationLogListView(PermissionRequiredMixin, ListView):
    """List all automation execution logs."""
    model = AutomationExecutionLog
    template_name = 'automation/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('automation', 'executed_by')

class WorkflowExecutionDetailView(PermissionRequiredMixin, DetailView):
    """Detail view for workflow execution logs."""
    model = WorkflowExecution
    template_name = 'automation/log_detail.html'
    required_permission = 'automation:read'

class AutomationLogDetailView(PermissionRequiredMixin, DetailView):
    """Detail view for automation execution logs."""
    model = AutomationExecutionLog
    template_name = 'automation/log_detail.html'
    required_permission = 'automation:read'

class SystemAutomationListView(PermissionRequiredMixin, ListView):
    """List system automations (cannot be deleted)."""
    model = Automation
    template_name = 'automation/system_list.html'
    context_object_name = 'automations'
    required_permission = 'automation:read'

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
    return redirect('automation:list')

# In your views.py, update the form handling

class AutomationConditionCreateView(PermissionRequiredMixin, CreateView):
    model = AutomationCondition
    form_class = AutomationConditionForm
    template_name = 'automation/condition_form.html'
    required_permission = 'automation:write'

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

class AutomationActionCreateView(PermissionRequiredMixin, CreateView):
    model = AutomationAction
    form_class = AutomationActionForm
    template_name = 'automation/action_form.html'
    required_permission = 'automation:write'

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
class WorkflowActionCreateView(PermissionRequiredMixin, CreateView):
    model = WorkflowAction
    fields = ['workflow_action_type', 'workflow_action_parameters', 'workflow_action_order', 'workflow_action_is_active']
    template_name = 'automation/action_form.html'
    required_permission = 'automation:write'

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

class WorkflowActionUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowAction
    fields = ['workflow_action_type', 'workflow_action_parameters', 'workflow_action_order', 'workflow_action_is_active']
    template_name = 'automation/action_form.html'
    required_permission = 'automation:write'

class WorkflowActionDeleteView(PermissionRequiredMixin, DeleteView):
    model = WorkflowAction
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    required_permission = 'automation:delete'

class WorkflowTriggerCreateView(PermissionRequiredMixin, CreateView):
    model = WorkflowTrigger
    fields = ['workflow_trigger_event', 'workflow_trigger_conditions', 'workflow_trigger_is_active']
    template_name = 'automation/condition_form.html'
    required_permission = 'automation:write'

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

class WorkflowTriggerUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowTrigger
    fields = ['workflow_trigger_event', 'workflow_trigger_conditions', 'workflow_trigger_is_active']
    template_name = 'automation/condition_form.html'
    required_permission = 'automation:write'

class WorkflowTriggerDeleteView(PermissionRequiredMixin, DeleteView):
    model = WorkflowTrigger
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    required_permission = 'automation:delete'


# Additional views for Workflow models
class WorkflowActionListView(PermissionRequiredMixin, ListView):
    model = WorkflowAction
    template_name = 'automation/workflow_action_list.html'
    context_object_name = 'workflow_actions'
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')


class WorkflowActionDetailView(PermissionRequiredMixin, DetailView):
    model = WorkflowAction
    template_name = 'automation/workflow_action_detail.html'
    required_permission = 'automation:read'


class WorkflowActionUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowAction
    fields = ['workflow_action_type', 'workflow_action_parameters', 'workflow_action_order', 'workflow_action_is_active']
    template_name = 'automation/workflow_action_form.html'
    success_url = '/automation/workflow-actions/'
    required_permission = 'automation:write'


class WorkflowActionDeleteView(PermissionRequiredMixin, DeleteView):
    model = WorkflowAction
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-actions/'
    required_permission = 'automation:delete'


class WorkflowExecutionListView(PermissionRequiredMixin, ListView):
    model = WorkflowExecution
    template_name = 'automation/workflow_execution_list.html'
    context_object_name = 'workflow_executions'
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')


class WorkflowExecutionDetailView(PermissionRequiredMixin, DetailView):
    model = WorkflowExecution
    template_name = 'automation/workflow_execution_detail.html'
    required_permission = 'automation:read'


class WorkflowExecutionUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowExecution
    fields = ['workflow_execution_status', 'workflow_execution_error_message', 'workflow_execution_completed_at']
    template_name = 'automation/workflow_execution_form.html'
    success_url = '/automation/workflow-executions/'
    required_permission = 'automation:write'


class WorkflowTriggerListView(PermissionRequiredMixin, ListView):
    model = WorkflowTrigger
    template_name = 'automation/workflow_trigger_list.html'
    context_object_name = 'workflow_triggers'
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('workflow')


class WorkflowTriggerDetailView(PermissionRequiredMixin, DetailView):
    model = WorkflowTrigger
    template_name = 'automation/workflow_trigger_detail.html'
    required_permission = 'automation:read'


class WorkflowTriggerUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowTrigger
    fields = ['workflow_trigger_event', 'workflow_trigger_conditions', 'workflow_trigger_is_active']
    template_name = 'automation/workflow_trigger_form.html'
    success_url = '/automation/workflow-triggers/'
    required_permission = 'automation:write'


class WorkflowTriggerDeleteView(PermissionRequiredMixin, DeleteView):
    model = WorkflowTrigger
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-triggers/'
    required_permission = 'automation:delete'


class WorkflowTemplateListView(PermissionRequiredMixin, ListView):
    model = WorkflowTemplate
    template_name = 'automation/workflow_template_list.html'
    context_object_name = 'workflow_templates'
    required_permission = 'automation:read'


class WorkflowTemplateDetailView(PermissionRequiredMixin, DetailView):
    model = WorkflowTemplate
    template_name = 'automation/workflow_template_detail.html'
    required_permission = 'automation:read'


class WorkflowTemplateUpdateView(PermissionRequiredMixin, UpdateView):
    model = WorkflowTemplate
    fields = ['workflow_template_name', 'workflow_template_description', 'workflow_template_trigger_type', 'workflow_template_builder_data', 'workflow_template_is_active']
    template_name = 'automation/workflow_template_form.html'
    success_url = '/automation/workflow-templates/'
    required_permission = 'automation:write'


class WorkflowTemplateDeleteView(PermissionRequiredMixin, DeleteView):
    model = WorkflowTemplate
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/workflow-templates/'
    required_permission = 'automation:delete'
