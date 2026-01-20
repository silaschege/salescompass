from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, Count
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import date

from core.models import User
from tenants.models import Tenant as TenantModel
from leads.models import Lead

from .models import Opportunity, OpportunityStage, AssignmentRule, PipelineType
from .forms import AssignmentRuleForm, OpportunityStageForm, PipelineTypeForm, OpportunityForm
from core.views import TenantAwareViewMixin
from core.permissions import ObjectPermissionRequiredMixin
from commissions.models import Quota
from .utils import calculate_weighted_forecast, calculate_forecast_accuracy, check_forecast_alerts, get_win_loss_stats
from .models import ForecastSnapshot
from engagement.utils import log_engagement_event


class OpportunityListView(LoginRequiredMixin, TenantAwareViewMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 20  # Add pagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('account', 'stage', 'owner')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate total value
        opportunities = self.get_queryset()
        total_value = sum(float(opp.amount) for opp in opportunities)
        context['total_value'] = total_value
        
        # Calculate weighted value
        weighted_value = sum(float(opp.weighted_value) for opp in opportunities)
        context['weighted_value'] = weighted_value
        
        # Calculate win rate
        total_opportunities = opportunities.count()
        won_opportunities = opportunities.filter(stage__is_won=True).count()
        win_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
        context['win_rate'] = win_rate
        
        # Add stages for filter dropdown
        if hasattr(self.request.user, 'tenant_id'):
            context['stages'] = OpportunityStage.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).order_by('order')
            
            # Add owners for filter dropdown
            context['owners'] = User.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).distinct()
            
            # Add accounts for filter dropdown
            from accounts.models import Account
            context['accounts'] = Account.objects.filter(
                tenant_id=self.request.user.tenant_id
            ).distinct()
        else:
            context['stages'] = OpportunityStage.objects.none()
            context['owners'] = User.objects.none()
            from accounts.models import Account
            context['accounts'] = Account.objects.none()
        
        return context



class OpportunityDetailView(LoginRequiredMixin, TenantAwareViewMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/opportunity_detail.html'
    context_object_name = 'opportunity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all stages for this tenant
        stages = OpportunityStage.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).order_by('order')
        
        context['stages'] = stages
        return context





class OpportunityCreateView(LoginRequiredMixin, TenantAwareViewMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunities:opportunity_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Handle case where tenant doesn't exist
        return kwargs
        
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                tenant = TenantModel.objects.get(id=self.request.user.tenant_id)
                form.instance.tenant = tenant
            except TenantModel.DoesNotExist:
                messages.error(self.request, 'Unable to assign tenant to opportunity.')
                return self.form_invalid(form)
        messages.success(self.request, 'Opportunity created successfully.')
        response = super().form_valid(form)
        

        return response
        
        return response



class OpportunityUpdateView(LoginRequiredMixin, TenantAwareViewMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunities:opportunity_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Handle case where tenant doesn't exist
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


class AssignmentRuleListView(ObjectPermissionRequiredMixin, ListView):
    model = AssignmentRule
    template_name = 'opportunities/assignment_rule_list.html'
    context_object_name = 'assignment_rules'
    permission_action = 'view'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current tenant and prefetch related objects
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.select_related('rule_type_ref', 'assigned_to')


class AssignmentRuleCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'opportunities/assignment_rule_form.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    permission_action = 'add'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Continue without tenant if it doesn't exist
        return kwargs
    
    def form_valid(self, form):
        # Set tenant automatically
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                tenant = TenantModel.objects.get(id=self.request.user.tenant_id)
                form.instance.tenant_id = self.request.user.tenant_id
            except TenantModel.DoesNotExist:
                messages.error(self.request, 'Unable to assign tenant to assignment rule.')
                return self.form_invalid(form)
        messages.success(self.request, 'Assignment rule created successfully.')
        return super().form_valid(form)


class AssignmentRuleUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = AssignmentRule
    form_class = AssignmentRuleForm
    template_name = 'opportunities/assignment_rule_form.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    permission_action = 'change'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass the current tenant to the form
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Continue without tenant if it doesn't exist
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Assignment rule updated successfully.')
        return super().form_valid(form)


class AssignmentRuleDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = AssignmentRule
    template_name = 'opportunities/assignment_rule_confirm_delete.html'
    success_url = reverse_lazy('opportunities:assignment_rule_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Assignment rule deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Pipeline Stage Management
class OpportunityStageListView(ObjectPermissionRequiredMixin, ListView):
    model = OpportunityStage
    template_name = 'opportunities/opportunity_stage_list.html'
    context_object_name = 'stages'
    permission_action = 'view'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.order_by('order')


class OpportunityStageCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = OpportunityStage
    form_class = OpportunityStageForm
    template_name = 'opportunities/opportunity_stage_form.html'
    success_url = reverse_lazy('opportunities:stage_list')
    permission_action = 'add'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Continue without tenant if it doesn't exist
        return kwargs
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                tenant = TenantModel.objects.get(id=self.request.user.tenant_id)
                form.instance.tenant_id = self.request.user.tenant_id
            except TenantModel.DoesNotExist:
                messages.error(self.request, 'Unable to assign tenant to pipeline stage.')
                return self.form_invalid(form)
        messages.success(self.request, 'Pipeline stage created successfully.')
        return super().form_valid(form)


class OpportunityStageUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = OpportunityStage
    form_class = OpportunityStageForm
    template_name = 'opportunities/opportunity_stage_form.html'
    success_url = reverse_lazy('opportunities:stage_list')
    permission_action = 'change'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'tenant_id') and self.request.user.tenant_id:
            try:
                kwargs['tenant'] = TenantModel.objects.get(id=self.request.user.tenant_id)
            except TenantModel.DoesNotExist:
                pass  # Continue without tenant if it doesn't exist
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Pipeline stage updated successfully.')
        return super().form_valid(form)

class OpportunityStageDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = OpportunityStage
    template_name = 'opportunities/opportunity_stage_confirm_delete.html'
    success_url = reverse_lazy('opportunities:stage_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pipeline stage deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Pipeline Type Management
class PipelineTypeListView(ObjectPermissionRequiredMixin, ListView):
    model = PipelineType
    template_name = 'opportunities/pipeline_type_list.html'
    context_object_name = 'pipeline_types'
    permission_action = 'view'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'tenant_id'):
            queryset = queryset.filter(tenant_id=self.request.user.tenant_id)
        return queryset.order_by('order')


class PipelineTypeCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'opportunities/pipeline_type_form.html'
    success_url = reverse_lazy('opportunities:type_list')
    permission_action = 'add'
    
    def form_valid(self, form):
        if hasattr(self.request.user, 'tenant_id'):
            form.instance.tenant_id = self.request.user.tenant_id
        messages.success(self.request, 'Pipeline type created successfully.')
        return super().form_valid(form)


class PipelineTypeUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = PipelineType
    form_class = PipelineTypeForm
    template_name = 'opportunities/pipeline_type_form.html'
    success_url = reverse_lazy('opportunities:type_list')
    permission_action = 'change'
    
    def form_valid(self, form):
        messages.success(self.request, 'Pipeline type updated successfully.')
        return super().form_valid(form)


class PipelineTypeDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = PipelineType
    template_name = 'opportunities/pipeline_type_confirm_delete.html'
    success_url = reverse_lazy('opportunities:type_list')
    permission_action = 'delete'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Pipeline type deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Base Dashboard View
class DashboardBaseView(ObjectPermissionRequiredMixin, TemplateView):
    """
    Base class for all dashboard views
    """
    permission_action = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get common context data for dashboards
        context['tenant_id'] = user.tenant_id
        context['current_date'] = timezone.now().date()
        
        return context


# Sales Velocity Dashboard View
class SalesVelocityDashboardView(DashboardBaseView):
    """
    Dashboard showing sales velocity metrics and trends.
    """
    template_name = 'opportunities/sales_velocity_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get opportunities for this tenant
        opportunities = Opportunity.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).select_related('account', 'owner', 'stage')
        
        # Calculate overall sales velocity metrics
        total_velocity = 0
        for opp in opportunities:
            total_velocity += opp.calculate_sales_velocity()
        avg_sales_velocity = total_velocity / opportunities.count() if opportunities.count() > 0 else 0
        
        # Calculate pipeline velocity
        total_weighted_value = sum(opp.weighted_value for opp in opportunities)
        pipeline_velocity = total_weighted_value / 30 if total_weighted_value > 0 else 0  # Per day average
        
        # Calculate conversion rate
        total_opportunities = opportunities.count()
        won_opportunities = opportunities.filter(stage__is_won=True).count()
        conversion_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
        
        # Calculate average sales cycle
        if won_opportunities > 0:
            avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in opportunities.filter(stage__is_won=True)) / won_opportunities
        else:
            # For open opportunities, estimate based on time open
            open_opps = opportunities.filter(stage__is_won=False)
            if open_opps.count() > 0:
                avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in open_opps) / open_opps.count()
            else:
                avg_sales_cycle = 0
        
        # Get sales velocity trend
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
        stages = OpportunityStage.objects.filter(tenant_id=self.request.user.tenant_id)
        stage_labels = [stage.opportunity_stage_name for stage in stages]
        stage_counts = [opportunities.filter(stage=stage).count() for stage in stages]
        stage_values = [sum(opp.amount for opp in opportunities.filter(stage=stage)) for stage in stages]
        
        context.update({
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
        })
        
        return context


# Forecast Dashboard View
class ForecastDashboardView(DashboardBaseView):
    """
    Dashboard showing sales forecast metrics and trends.
    """
    template_name = 'opportunities/forecast_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get forecast data
        forecast_data = calculate_weighted_forecast(tenant_id=self.request.user.tenant_id)
        context['forecast_data'] = forecast_data
        
        # Get recent forecast alerts
        context['forecast_alerts'] = check_forecast_alerts(tenant_id=self.request.user.tenant_id)
        
        # Get quota information
        current_date = context['current_date']
        total_quota = Quota.objects.filter(
            user__tenant_id=self.request.user.tenant_id,
            period_start__lte=current_date,
            period_end__gte=current_date
        ).aggregate(total=Sum('target_amount'))['total'] or 0
        
        context['total_quota'] = float(total_quota)
        
        if context['total_quota'] > 0 and 'weighted_forecast' in forecast_data:
            context['quota_attainment'] = (forecast_data['weighted_forecast'] / context['total_quota']) * 100
        else:
            context['quota_attainment'] = 0
            
        return context


# Opportunity Funnel Analysis View
class OpportunityFunnelAnalysisView(DashboardBaseView):
    """
    View showing opportunity conversion rates between stages.
    """
    template_name = 'opportunities/opportunity_funnel_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all stages for this tenant
        stages = OpportunityStage.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).order_by('order')
        
        # Get all opportunities for this tenant
        opportunities = Opportunity.objects.filter(
            tenant_id=self.request.user.tenant_id
        )
        
        # Calculate funnel data
        funnel_data = []
        previous_count = opportunities.count()
        
        for stage in stages:
            current_count = opportunities.filter(stage=stage).count()
            conversion_rate = (current_count / previous_count * 100) if previous_count > 0 else 0
            funnel_data.append({
                'stage': stage.opportunity_stage_name,
                'count': current_count,
                'conversion_rate': conversion_rate
            })
            previous_count = current_count
        
        context['funnel_data'] = funnel_data
        
        return context


# Win/Loss Analysis View
class WinLossAnalysisView(DashboardBaseView):
    """
    View showing win/loss analysis for opportunities.
    """
    template_name = 'opportunities/win_loss_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get win/loss statistics
        stats = get_win_loss_stats(tenant_id=self.request.user.tenant_id)
        context['stats'] = stats
        
        return context


# === Pipeline Kanban View ===
class PipelineKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    """
    Kanban board view for opportunity pipeline.
    Shows opportunities organized by stage with drag-and-drop functionality.
    """
    template_name = 'opportunities/pipeline_kanban.html'
    permission_action = 'view'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = getattr(user, 'tenant_id', None)
        
        # Get all stages for this tenant
        stages = OpportunityStage.objects.filter(
            tenant_id=tenant_id
        ).order_by('order')
        
        # Get all opportunities for this tenant
        opportunities = Opportunity.objects.filter(
            tenant_id=tenant_id
        ).select_related('account', 'owner', 'stage')
        
        # Calculate overall stats
        total_value = opportunities.aggregate(total=Sum('amount'))['total'] or 0
        total_count = opportunities.count()
        
        # Calculate weighted value (sum of amount * probability)
        weighted_value = sum(
            float(opp.amount) * opp.probability
            for opp in opportunities
        )
        
        # Organize opportunities by stage
        today = date.today()
        stage_data = []
        
        for stage in stages:
            stage_opps = opportunities.filter(stage=stage)
            
            # Prepare opportunity data with additional fields
            opp_list = []
            for opp in stage_opps:
                opp_list.append({
                    'id': opp.id,
                    'name': opp.opportunity_name,
                    'amount': opp.amount,
                    'probability': opp.probability,
                    'probability_percent': int(opp.probability * 100),
                    'close_date': opp.close_date,
                    'is_overdue': opp.close_date < today if opp.close_date else False,
                    'account': {
                        'name': opp.account.account_name if opp.account else 'No Account'
                    }
                })
            
            stage_total = stage_opps.aggregate(total=Sum('amount'))['total'] or 0
            
            stage_data.append({
                'id': stage.id,
                'name': stage.opportunity_stage_name,
                'order': stage.order,
                'probability': stage.probability,
                'is_won': stage.is_won,
                'is_lost': stage.is_lost,
                'opportunities': opp_list,
                'opportunity_count': len(opp_list),
                'total_value': stage_total
            })
        
        context['stages'] = stage_data
        context['total_value'] = total_value
        context['weighted_value'] = weighted_value
        context['total_count'] = total_count
        
        return context


# === AJAX Endpoint for Stage Updates ===
@require_POST
def update_opportunity_stage(request, opportunity_id):
    """
    AJAX endpoint to update an opportunity's stage.
    Updates the stage and optionally the probability based on the new stage.
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        new_stage_id = data.get('stage_id')
        
        if not new_stage_id:
            return JsonResponse({
                'success': False,
                'message': 'Stage ID is required'
            }, status=400)
        
        # Get the opportunity
        opportunity = Opportunity.objects.get(
            id=opportunity_id,
            tenant_id=request.user.tenant_id
        )
        
        # Get the new stage
        new_stage = OpportunityStage.objects.get(
            id=new_stage_id,
            tenant_id=request.user.tenant_id
        )
        
        # Update the opportunity
        old_stage = opportunity.stage
        opportunity.stage = new_stage
        
        # Update probability to match the stage's default probability
        # Convert from 0-100 to 0-1 if needed
        if hasattr(new_stage, 'probability'):
            if new_stage.probability > 1:
                opportunity.probability = new_stage.probability / 100
            else:
                opportunity.probability = new_stage.probability
        
        opportunity.save()
        

        return JsonResponse({
            'success': True,
            'message': f'Moved to {new_stage.opportunity_stage_name}',
            'old_stage': old_stage.opportunity_stage_name if old_stage else None,
            'new_stage': new_stage.opportunity_stage_name,
            'new_probability': opportunity.probability
        })
        
    except Opportunity.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Opportunity not found'
        }, status=404)
    
    except OpportunityStage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Stage not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# === AJAX Endpoint for Forecast Data ===
@require_POST
def get_forecast_data(request):
    """
    AJAX endpoint to get updated forecast data.
    """
    try:
        # Get forecast data
        forecast_data = calculate_weighted_forecast(tenant_id=request.user.tenant_id)
        
        return JsonResponse({
            'success': True,
            'forecast_data': forecast_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)