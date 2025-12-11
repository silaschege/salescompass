from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.core.cache import cache
from django.conf import settings
from .models import DashboardWidget, WidgetType as DashboardWidgetType, WidgetCategory as DashboardWidgetCategory, DashboardConfig
from .forms import DashboardWidgetForm, WidgetTypeForm, WidgetCategoryForm
from tenants.models import Tenant as TenantModel
from core.object_permissions import WidgetTypePermissionMixin, WidgetCategoryPermissionMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from core.models import User
import json



class CockpitView(LoginRequiredMixin, TemplateView):
    """Main dashboard cockpit view - shows user's default or first available dashboard"""
    template_name = 'dashboard/cockpit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's dashboards
        user_dashboards = DashboardConfig.objects.filter(user=user).order_by('-is_default', '-config_created_at')
        
        # Get the default dashboard or first available
        current_dashboard = user_dashboards.filter(is_default=True).first()
        if not current_dashboard:
            current_dashboard = user_dashboards.first()
        
        context['user_dashboards'] = user_dashboards
        context['current_dashboard'] = current_dashboard
        context['available_widgets'] = DashboardWidget.objects.filter(widget_is_active=True)
        
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin-specific dashboard with system-wide metrics"""
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get system-wide stats
        context['active_tenants_count'] = TenantModel.objects.filter(is_active=True).count()
        context['total_users_count'] = User.objects.filter(is_active=True).count()
        context['mrr'] = 0  # Would calculate from billing
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['recent_subscriptions'] = []  # Would get from billing
        
        return context


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    """Manager-specific dashboard with team and pipeline metrics"""
    template_name = 'dashboard/manager_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Team performance metrics (placeholder - would pull from leads, opportunities, etc.)
        context['team_leads_count'] = 0
        context['team_opportunities_count'] = 0
        context['team_revenue'] = 0
        context['team_members'] = []
        context['pipeline_stages'] = []
        
        return context


class SupportDashboardView(LoginRequiredMixin, TemplateView):
    """Support team dashboard with case metrics"""
    template_name = 'dashboard/support_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Support metrics (placeholder - would pull from cases app)
        context['open_cases_count'] = 0
        context['resolved_today_count'] = 0
        context['avg_resolution_time'] = 0
        context['sla_compliance'] = 0
        context['recent_cases'] = []
        
        return context


class DashboardRenderView(LoginRequiredMixin, TemplateView):
    """Render a specific dashboard by ID"""
    template_name = 'dashboard/render.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = kwargs.get('pk')
        
        dashboard = get_object_or_404(DashboardConfig, pk=dashboard_id, user=self.request.user)
        context['dashboard'] = dashboard
        context['layout'] = dashboard.layout or {}
        context['widget_settings'] = dashboard.widget_settings or {}
        
        return context


class SaveDashboardView(LoginRequiredMixin, View):
    """API endpoint to save dashboard configuration"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            dashboard_id = data.get('dashboard_id')
            
            if dashboard_id:
                dashboard = get_object_or_404(DashboardConfig, pk=dashboard_id, user=request.user)
            else:
                dashboard = DashboardConfig(user=request.user)
            
            dashboard.name = data.get('name', dashboard.name or 'My Dashboard')
            dashboard.layout = data.get('layout', {})
            dashboard.widget_settings = data.get('widget_settings', {})
            dashboard.is_default = data.get('is_default', False)
            dashboard.save()
            
            return JsonResponse({
                'success': True,
                'dashboard_id': dashboard.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


def dynamic_choices_dashboard(request):
    """
    Dashboard view for managing all dynamic choice models in one place
    """
    # Get counts for each dynamic choice model
    context = {
        'widget_types_count': DashboardWidgetType.objects.count(),
        'widget_categories_count': DashboardWidgetCategory.objects.count(),
        'dashboard_widgets_count': DashboardWidget.objects.filter(widget_is_active=True).count(),
    }
    return render(request, 'dashboard/dynamic_choices_dashboard.html', context)


class WidgetTypeListView(LoginRequiredMixin, WidgetTypePermissionMixin, ListView):
    model = DashboardWidgetType
    template_name = 'dashboard/widget_type_list.html'
    context_object_name = 'widget_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class WidgetTypeCreateView(LoginRequiredMixin, WidgetTypePermissionMixin, CreateView):
    model = DashboardWidgetType
    form_class = WidgetTypeForm
    template_name = 'dashboard/widget_type_form.html'
    success_url = reverse_lazy('dashboard:widget_type_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Widget type created successfully.')
        return super().form_valid(form)


class WidgetTypeUpdateView(LoginRequiredMixin, WidgetTypePermissionMixin, UpdateView):
    model = DashboardWidgetType
    form_class = WidgetTypeForm
    template_name = 'dashboard/widget_type_form.html'
    success_url = reverse_lazy('dashboard:widget_type_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Widget type updated successfully.')
        return super().form_valid(form)


class WidgetTypeDeleteView(LoginRequiredMixin, WidgetTypePermissionMixin, DeleteView):
    model = DashboardWidgetType
    template_name = 'dashboard/widget_type_confirm_delete.html'
    success_url = reverse_lazy('dashboard:widget_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Widget type deleted successfully.')
        return super().delete(request, *args, **kwargs)


class WidgetCategoryListView(LoginRequiredMixin, WidgetCategoryPermissionMixin, ListView):
    model = DashboardWidgetCategory
    template_name = 'dashboard/widget_category_list.html'
    context_object_name = 'widget_categories'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset


class WidgetCategoryCreateView(LoginRequiredMixin, WidgetCategoryPermissionMixin, CreateView):
    model = DashboardWidgetCategory
    form_class = WidgetCategoryForm
    template_name = 'dashboard/widget_category_form.html'
    success_url = reverse_lazy('dashboard:widget_category_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Widget category created successfully.')
        return super().form_valid(form)


class WidgetCategoryUpdateView(LoginRequiredMixin, WidgetCategoryPermissionMixin, UpdateView):
    model = DashboardWidgetCategory
    form_class = WidgetCategoryForm
    template_name = 'dashboard/widget_category_form.html'
    success_url = reverse_lazy('dashboard:widget_category_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Widget category updated successfully.')
        return super().form_valid(form)


class WidgetCategoryDeleteView(LoginRequiredMixin, WidgetCategoryPermissionMixin, DeleteView):
    model = DashboardWidgetCategory
    template_name = 'dashboard/widget_category_confirm_delete.html'
    success_url = reverse_lazy('dashboard:widget_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Widget category deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def get_dynamic_choices_api(request, model_name):
    """
    API endpoint to fetch dynamic choices for a specific model with caching
    """
    tenant_id = request.user.tenant_id if hasattr(request.user, 'tenant_id') else None
    
    if not tenant_id:
        return JsonResponse({'error': 'No tenant associated with user'}, status=400)
    
    # Generate cache key
    cache_key = f"dynamic_choices_{model_name.lower()}_{tenant_id}"
    
    # Try to get from cache first
    cached_choices = cache.get(cache_key)
    if cached_choices is not None:
        return JsonResponse(cached_choices, safe=False)
    
    # Map model names to actual models
    model_map = {
        'widgettype': DashboardWidgetType,
        'widgetcategory': DashboardWidgetCategory,
    }
    
    model_class = model_map.get(model_name.lower())
    
    if not model_class:
        return JsonResponse({'error': 'Invalid choice model'}, status=400)
    
    try:
        choices = list(model_class.objects.filter(tenant_id=tenant_id, is_active=True).values('id', 'name', 'label'))
        
        # Cache the results for 15 minutes (900 seconds)
        cache.set(cache_key, choices, 900)
        
        return JsonResponse(choices, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
