"""
Dashboard Wizard Views
Handles the 3-step dashboard creation wizard workflow.
"""
from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import DashboardConfig, DashboardWidget
from .model_introspection import get_available_models, get_model_fields, get_default_model_for_widget
import json


class DashboardWizardMixin(LoginRequiredMixin):
    """Base mixin for wizard steps with session management"""
    
    def get_wizard_data(self):
        """Retrieve wizard data from session"""
        return self.request.session.get('dashboard_wizard', {})
    
    def save_wizard_data(self, data):
        """Save wizard data to session"""
        wizard_data = self.get_wizard_data()
        wizard_data.update(data)
        self.request.session['dashboard_wizard'] = wizard_data
        self.request.session.modified = True
    
    def clear_wizard_data(self):
        """Clear wizard session data"""
        if 'dashboard_wizard' in self.request.session:
            del self.request.session['dashboard_wizard']


class DashboardWizardStep1View(DashboardWizardMixin, TemplateView):
    """Step 1: Dashboard name and module selection"""
    template_name = 'dashboard/wizard/step1.html'
    
    # Preset dashboard templates
    PRESET_TEMPLATES = [
        {
            'id': 'blank',
            'name': 'Blank Dashboard',
            'description': 'Start from scratch with your own modules',
            'icon': 'bi-grid-3x3-gap',
            'modules': []
        },
        {
            'id': 'sales_performance',
            'name': 'Sales Performance',
            'description': 'Track sales metrics, revenue, and top performers',
            'icon': 'bi-graph-up-arrow',
            'modules': ['revenue', 'pipeline', 'leaderboard']
        },
        {
            'id': 'customer_acquisition',
            'name': 'Customer Acquisition',
            'description': 'Monitor lead sources and conversion funnel',
            'icon': 'bi-person-plus',
            'modules': ['leads', 'activity']
        },
        {
            'id': 'leads_dashboard',
            'name': 'Leads Dashboard',
            'description': 'Focus on lead management and conversion',
            'icon': 'bi-person-check',
            'modules': ['leads']
        },
        {
            'id': 'support_overview',
            'name': 'Support Overview',
            'description': 'Track cases and customer satisfaction',
            'icon': 'bi-headset',
            'modules': ['cases', 'nps']
        }
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available modules filtered by permission
        all_modules = DashboardWidget.objects.filter(is_active=True).order_by('category', 'name')
        available_modules = [
            widget for widget in all_modules 
            if not widget.required_permission or self.request.user.has_perm(widget.required_permission)
        ]
        
        context['preset_templates'] = self.PRESET_TEMPLATES
        context['available_modules'] = available_modules
        context['wizard_data'] = self.get_wizard_data()
        
        return context
    
    def post(self, request):
        """Save step 1 data and proceed to step 2"""
        data = {
            'dashboard_name': request.POST.get('dashboard_name', 'My Dashboard'),
            'template_id': request.POST.get('template_id', 'blank'),
            'selected_modules': request.POST.getlist('modules')
        }
        
        self.save_wizard_data(data)
        return redirect('dashboard:wizard_step2')


class DashboardWizardStep2View(DashboardWizardMixin, TemplateView):
    """Step 2: Configure module settings"""
    template_name = 'dashboard/wizard/step2.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wizard_data = self.get_wizard_data()
        
        # Get selected module IDs from step 1
        selected_module_ids = wizard_data.get('selected_modules', [])
        
        # Get selected modules and add default model for each
        selected_modules = DashboardWidget.objects.filter(
            widget_type__in=selected_module_ids,
            is_active=True
        )
        
        # Create widget configs with default models
        widget_configs = []
        for widget in selected_modules:
            widget_configs.append({
                'widget': widget,
                'default_model': get_default_model_for_widget(widget.widget_type)
            })
        
        context['widget_configs'] = widget_configs
        context['wizard_data'] = wizard_data
        context['available_models'] = get_available_models()
        
        return context
    
    def post(self, request):
        """Save module configurations and proceed to step 3"""
        module_configs = {}
        
        # Collect configurations for each module
        for module_id in request.POST.getlist('configured_modules'):
            # Parse filters from POST data
            filters = []
            filter_fields = request.POST.getlist(f'{module_id}_filter_field')
            filter_operators = request.POST.getlist(f'{module_id}_filter_operator')
            filter_values = request.POST.getlist(f'{module_id}_filter_value')
            
            for i in range(len(filter_fields)):
                if filter_fields[i]:  # Only add if field is selected
                    filters.append({
                        'field': filter_fields[i],
                        'operator': filter_operators[i] if i < len(filter_operators) else 'exact',
                        'value': filter_values[i] if i < len(filter_values) else ''
                    })
            
            module_configs[module_id] = {
                'model': request.POST.get(f'{module_id}_model', ''),
                'time_range': int(request.POST.get(f'{module_id}_time_range', 30)),
                'aggregation': request.POST.get(f'{module_id}_aggregation', 'count'),
                'aggregation_field': request.POST.get(f'{module_id}_aggregation_field', ''),
                'sorting': request.POST.get(f'{module_id}_sorting', 'desc'),
                'filters': filters
            }
        
        self.save_wizard_data({'module_configs': module_configs})
        return redirect('dashboard:wizard_step3')


class ModelFieldsAPIView(LoginRequiredMixin, View):
    """API endpoint to fetch fields for a selected model"""
    
    def get(self, request):
        model_id = request.GET.get('model')
        if not model_id:
            return JsonResponse({'error': 'Model ID is required'}, status=400)
            
        fields = get_model_fields(model_id)
        return JsonResponse({'fields': fields})


class DashboardWizardStep3View(DashboardWizardMixin, TemplateView):
    """Step 3: Arrange layout and preview"""
    template_name = 'dashboard/wizard/step3.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wizard_data = self.get_wizard_data()
        
        # Get selected modules with their configurations
        selected_module_ids = wizard_data.get('selected_modules', [])
        selected_modules = list(DashboardWidget.objects.filter(
            widget_type__in=selected_module_ids,
            is_active=True
        ))
        
        # Set default position based on index
        for index, widget in enumerate(selected_modules):
            if index < 2:
                widget.default_position = 'top'
            elif index < 4:
                widget.default_position = 'middle'
            else:
                widget.default_position = 'bottom'
        
        context['selected_modules'] = selected_modules
        context['wizard_data'] = wizard_data
        context['module_configs'] = wizard_data.get('module_configs', {})
        
        return context


class DashboardWizardSaveView(DashboardWizardMixin, View):
    """Save the dashboard and clear wizard session"""
    
    def post(self, request):
        try:
            wizard_data = self.get_wizard_data()
            layout_data = json.loads(request.body)
            
            # Create dashboard
            dashboard = DashboardConfig.objects.create(
                user=request.user,
                name=wizard_data.get('dashboard_name', 'My Dashboard'),
                layout=layout_data.get('layout', {}),
                widget_settings=wizard_data.get('module_configs', {})
            )
            
            # Clear wizard session
            self.clear_wizard_data()
            
            return JsonResponse({
                'success': True,
                'dashboard_id': dashboard.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)