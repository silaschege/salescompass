from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages

from core.models import User
from tenants.models import Tenant as TenantModel
from leads.models import Lead

from .models import Opportunity, OpportunityStage, AssignmentRule, PipelineType
from .forms import AssignmentRuleForm, OpportunityStageForm, PipelineTypeForm, OpportunityForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.views import TenantAwareViewMixin

class OpportunityListView(LoginRequiredMixin, TenantAwareViewMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/opportunity_list.html'
    context_object_name = 'opportunities'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('account', 'stage', 'owner')

class OpportunityDetailView(LoginRequiredMixin, TenantAwareViewMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/opportunity_detail.html'
    context_object_name = 'opportunity'

class OpportunityCreateView(LoginRequiredMixin, TenantAwareViewMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunities:opportunity_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
        
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Opportunity created successfully.')
        return super().form_valid(form)

class OpportunityUpdateView(LoginRequiredMixin, TenantAwareViewMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunities:opportunity_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Opportunity updated successfully.')
        return super().form_valid(form)

class OpportunityDeleteView(LoginRequiredMixin, TenantAwareViewMixin, DeleteView):
    model = Opportunity
    template_name = 'opportunities/opportunity_confirm_delete.html'
    success_url = reverse_lazy('opportunities:opportunity_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Opportunity deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def sales_velocity_dashboard(request):
    """
    Display the Sales Velocity dashboard with key metrics.
    """
    # Calculate overall sales velocity metrics
    opportunities = Opportunity.objects.all()
    
    # Calculate average sales velocity
    total_velocity = 0
    for opp in opportunities:
        total_velocity += opp.calculate_sales_velocity()
    avg_sales_velocity = total_velocity / opportunities.count() if opportunities.count() > 0 else 0
    
    # Calculate pipeline velocity
    pipeline_velocity = 0  # Using the method we added to the Opportunity model
    # For now, using a simplified calculation
    total_weighted_value = sum(opp.weighted_value for opp in opportunities)
    pipeline_velocity = total_weighted_value / 30 if total_weighted_value > 0 else 0  # Per day average
    
    # Calculate conversion rate
    total_opportunities = opportunities.count()
    won_opportunities = opportunities.filter(stage__is_won=True).count()
    conversion_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    
    # Calculate average sales cycle
    avg_sales_cycle = 0  # Using the method we added to the Opportunity model
    # For now, using a simplified calculation
    if won_opportunities > 0:
        avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in opportunities.filter(stage__is_won=True)) / won_opportunities
    else:
        # For open opportunities, estimate based on time open
        open_opps = opportunities.filter(stage__is_won=False)
        if open_opps.count() > 0:
            avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in open_opps) / open_opps.count()
    
    # Get sales velocity trend using the method we added to the Opportunity model
    velocity_trend_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    velocity_trend_data = [1000, 1200, 1100, 1300, 1400, 1500]  # Placeholder values
    
    # Get top opportunities by velocity
    top_velocity_opportunities = []
    for opp in opportunities:
        opp.days_open = (opp.updated_at.date() - opp.created_at.date()).days if opp.created_at else 1
        top_velocity_opportunities.append(opp)
    top_velocity_opportunities.sort(key=lambda x: x.calculate_sales_velocity(), reverse=True)
    top_velocity_opportunities = top_velocity_opportunities[:10]  # Top 10
    
    # Get opportunities by stage
    stages = OpportunityStage.objects.all()
    stage_labels = [stage.opportunity_stage_name for stage in stages]
    stage_counts = [opportunities.filter(stage=stage).count() for stage in stages]
    stage_values = [sum(opp.amount for opp in opportunities.filter(stage=stage)) for stage in stages]
    
    context = {
        'avg_sales_velocity': avg_sales_velocity,
        'pipeline_velocity': pipeline_velocity,
        'conversion_rate': conversion_rate,
        'avg_sales_cycle': avg_sales_cycle,
        'velocity_trend_labels': velocity_trend_labels,
        'velocity_trend_data': velocity_trend_data,
        'top_velocity_opportunities': top_velocity_opportunities,
        'stage_labels': stage_labels,
        'stage_counts': stage_counts,
        'stage_values': stage_values,
    }
    
    return render(request, 'opportunities/sales_velocity_dashboard.html', context)


@login_required
def sales_velocity_analysis(request):
    """
    Detailed sales velocity analysis.
    """
    # Implementation would go here
    pass


@login_required
def opportunity_funnel_analysis(request):
    """
    Opportunity funnel analysis showing conversion rates between stages.
    """
    # Implementation would go here
    pass


class AssignmentRuleListView(ListView):
    model = AssignmentRule
    template_name = 'opportunities/assignment_rule_list.html'
    context_object_name = 'assignment_rules'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('rule_type_ref', 'assigned_to')


class AssignmentRuleCreateView(CreateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'opportunities/assignment_rule_form.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    
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
    template_name = 'opportunities/assignment_rule_form.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    
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
    template_name = 'opportunities/assignment_rule_confirm_delete.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Pipeline Stage Management
class OpportunityStageListView(ListView):
    model = OpportunityStage
    template_name = 'opportunities/opportunity_stage_list.html'
    context_object_name = 'stages'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.order_by('order')

class OpportunityStageCreateView(CreateView):
    model = OpportunityStage
    form_class = OpportunityStageForm
    template_name = 'opportunities/opportunity_stage_form.html'
    success_url = reverse_lazy('opportunities:stage_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Pipeline stage created successfully.')
        return super().form_valid(form)

class OpportunityStageUpdateView(UpdateView):
    model = OpportunityStage
    form_class = OpportunityStageForm
    template_name = 'opportunities/opportunity_stage_form.html'
    success_url = reverse_lazy('opportunities:stage_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id'):
            kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Pipeline stage updated successfully.')
        return super().form_valid(form)

class OpportunityStageDeleteView(DeleteView):
    model = OpportunityStage
    template_name = 'opportunities/opportunity_stage_confirm_delete.html'
    success_url = reverse_lazy('opportunities:stage_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pipeline stage deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Pipeline Type Management
class PipelineTypeListView(ListView):
    model = PipelineType
    template_name = 'opportunities/pipeline_type_list.html'
    context_object_name = 'pipeline_types'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.order_by('order')

class PipelineTypeCreateView(CreateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'opportunities/pipeline_type_form.html'
    success_url = reverse_lazy('opportunities:type_list')
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Pipeline type created successfully.')
        return super().form_valid(form)

class PipelineTypeUpdateView(UpdateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'opportunities/pipeline_type_form.html'
    success_url = reverse_lazy('opportunities:type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Pipeline type updated successfully.')
        return super().form_valid(form)

class PipelineTypeDeleteView(DeleteView):
    model = PipelineType
    template_name = 'opportunities/pipeline_type_confirm_delete.html'
    success_url = reverse_lazy('opportunities:type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pipeline type deleted successfully.')
        return super().delete(request, *args, **kwargs)


from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from commissions.models import Quota
from .utils import calculate_weighted_forecast, calculate_forecast_accuracy, check_forecast_alerts
from .models import ForecastSnapshot

class RevenueForecastView(LoginRequiredMixin, TemplateView):
    template_name = 'opportunities/forecast_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'tenant'):
            tenant = self.request.user.tenant
        else:
             tenant = getattr(self.request.user, 'tenant', None)
             
        if not tenant:
             current_forecast = {'weighted_forecast': 0, 'total_pipeline': 0}
             context['current_forecast'] = current_forecast
             return context

        # 1. Current Forecast
        forecast_data = calculate_weighted_forecast(tenant_id=tenant.id)
        context['current_forecast'] = forecast_data
        
        # 2. Historical Trend (Snapshots)
        snapshots = ForecastSnapshot.objects.filter(
            tenant=tenant
        ).order_by('date')[:30]
        
        context['snapshot_labels'] = [s.date.strftime('%Y-%m-%d') for s in snapshots]
        context['snapshot_pipeline'] = [float(s.total_pipeline_value) for s in snapshots]
        context['snapshot_weighted'] = [float(s.weighted_forecast) for s in snapshots]
        
        # 3. Quota
        current_date = timezone.now().date()
        total_quota = Quota.objects.filter(
            user__tenant=tenant,
            period_start__lte=current_date,
            period_end__gte=current_date
        ).aggregate(total=Sum('target_amount'))['total'] or 0
        
        context['total_quota'] = float(total_quota)
        
        if context['total_quota'] > 0:
            context['quota_attainment'] = (context['current_forecast']['weighted_forecast'] / context['total_quota']) * 100
        else:
            context['quota_attainment'] = 0
            
        # 4. Accuracy & Alerts
        context['accuracy_metrics'] = calculate_forecast_accuracy(tenant_id=tenant.id)
        context['forecast_alerts'] = check_forecast_alerts(tenant_id=tenant.id)
            
        return context
