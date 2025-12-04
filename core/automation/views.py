from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from core.permissions import PermissionRequiredMixin, require_permission
from .models import Automation, AutomationCondition, AutomationAction, Workflow, WorkflowTemplate
from .forms import AutomationForm, AutomationConditionForm, AutomationActionForm
from .utils import get_available_triggers
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from .models import AutomationExecutionLog
from .utils import emit_event, execute_automation
 
class AutomationListView(PermissionRequiredMixin, ListView):
    model = Workflow
    template_name = 'automation/list.html'
    context_object_name = 'automations'
    required_permission = 'automation:read'
    def get_queryset(self):
        # Ensure we're getting all automations, or apply specific filters
        return Workflow.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for automation in context['automations']:
            print(f"Automation ID: {automation.pk}")
        print(f"Automations count: {context['automations'].count()}")  # Debug line
        return context

class AutomationDetailView(PermissionRequiredMixin, DetailView):
    model = Workflow
    template_name = 'automation/detail.html'
    required_permission = 'automation:read'



class AutomationUpdateView(PermissionRequiredMixin, UpdateView):
    model = Workflow
    form_class = AutomationForm
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context


# Standardize on Workflow model throughout (since ListView uses it)
class AutomationCreateView(PermissionRequiredMixin, CreateView):
    model = Workflow  # Change from Automation to Workflow
    form_class = AutomationForm
    template_name = 'automation/form.html'
    success_url = '/automation/'
    required_permission = 'automation:write'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trigger_types'] = get_available_triggers()
        return context

class AutomationDeleteView(PermissionRequiredMixin, DeleteView):
    model = Workflow  # Change from Automation to Workflow
    template_name = 'automation/confirm_delete.html'
    success_url = '/automation/'
    required_permission = 'automation:delete'
    def delete(self, request, *args, **kwargs):
        automation = self.get_object()
        if automation.is_system:
            messages.error(request, "System automations cannot be deleted.")
            return redirect('automation:list')
        messages.success(request, f"Automation '{automation.name}' deleted.")
        return super().delete(request, *args, **kwargs)
    

#     link with other apps
#         from automation.utils import emit_event

# def create_account(request):
#     # ... account creation logic ...
#     account = Account.objects.create(...)
    
#     # Emit automation event
#     emit_event('account.created', {
#         'account_id': account.id,
#         'account_name': account.name,
#         'industry': account.industry,
#         'health_score': account.health_score,
#         'tenant_id': account.tenant_id,
#     })


# from automation.utils import emit_event

# def close_case_with_csat(case_id: int, csat_score: int, csat_comment: str = ""):
#     # ... CSAT logic ...
#     emit_event('case.csat_submitted', {
#         'case_id': case.id,
#         'account_id': case.account_id,
#         'csat_score': csat_score,
#         'csat_comment': csat_comment,
#         'tenant_id': case.tenant_id,
#     })




# # Automation settings
# AUTOMATION_ASYNC = True  # Use Celery for async execution
# AUTOMATION_MAX_EXECUTION_TIME = 30  # seconds
# AUTOMATION_LOG_RETENTION_DAYS = 30

# # Celery configuration
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# CELERY_TASK_ROUTES = {
#     'automation.tasks.execute_automation_task': {'queue': 'automation'},
# }

# Add these views to your existing views.py


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
            return JsonResponse({'error': str(e)}, status=400)


class AutomationLogListView(PermissionRequiredMixin, ListView):
    """List all automation execution logs."""
    model = AutomationExecutionLog
    template_name = 'automation/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    required_permission = 'automation:read'

    def get_queryset(self):
        return super().get_queryset().select_related('automation', 'executed_by')


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
        'templates': WorkflowTemplate.objects.filter(is_active=True),
        'module_config': MODULE_CONFIG,
        'module_config_json': json.dumps(MODULE_CONFIG) if MODULE_CONFIG else '{}'
    }
    
    if workflow_id:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        context['workflow'] = workflow
        context['workflow_id'] = workflow_id
        if hasattr(workflow, 'builder_data') and workflow.builder_data:
            context['workflow_data'] = json.dumps(workflow.builder_data)
            
    template_id = request.GET.get('template_id')
    if template_id and not workflow_id:
        template = get_object_or_404(WorkflowTemplate, id=template_id)
        context['workflow_data'] = json.dumps(template.builder_data)
        context['template_name'] = template.name
    
    return render(request, 'automation/workflow_builder.html', context)

@csrf_exempt
@require_permission('automation:write')
def save_workflow(request):
    """Save workflow from visual builder."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        from .models import Workflow, WorkflowTrigger, WorkflowAction
        
        data = json.loads(request.body)
        workflow_name = data.get('name')
        workflow_data = data.get('workflow_data', {})
        workflow_id = data.get('id')
        
        if not workflow_name:
            return JsonResponse({'error': 'Workflow name is required'}, status=400)
        
        # Handle update vs create
        if workflow_id:
            workflow = get_object_or_404(Workflow, id=workflow_id)
            workflow.name = workflow_name
            workflow.builder_data = workflow_data
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
                name=workflow_name,
                trigger_type=trigger_type,
                is_active=True,
                tenant_id=request.user.tenant_id if hasattr(request.user, 'tenant_id') else None,
                created_by=request.user if request.user.is_authenticated else None,
                builder_data=workflow_data
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
            'name': workflow.name,
            'trigger_type': workflow.trigger_type,
            # Add drawflow data here
        }
        
        return JsonResponse({
            'success': True,
            'workflow': workflow_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)