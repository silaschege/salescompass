import json
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.permissions import ObjectPermissionRequiredMixin
from .models import Opportunity, ForecastSnapshot, WinLossAnalysis, OpportunityStage
from .forms import OpportunityForm, WinLossAnalysisForm
from .utils import calculate_weighted_forecast, create_forecast_snapshot, get_win_loss_stats
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum, Count, Q

class OpportunityListView(ObjectPermissionRequiredMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/list.html'
    context_object_name = 'opportunities'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('account', 'owner')


class OpportunityKanbanView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'opportunities/kanban.html'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opportunities = self.get_queryset()
        context['opportunities'] = opportunities
        context['stage_choices'] = Opportunity._meta.get_field('stage').choices
        return context

    def get_queryset(self):
        from core.object_permissions import OpportunityObjectPolicy
        return OpportunityObjectPolicy.get_viewable_queryset(self.request.user, Opportunity.objects.all())


class OpportunityDetailView(ObjectPermissionRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/detail.html'
    context_object_name = 'opportunity'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all active stages ordered by sequence
        context['stages'] = OpportunityStage.objects.filter(
            tenant_id=self.request.user.tenant_id
        ).order_by('order')
        return context


class OpportunityCreateView(ObjectPermissionRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/form.html'
    success_url = '/opportunities/'
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Opportunity '{form.instance.name}' created!")
        return super().form_valid(form)


class OpportunityUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/form.html'
    success_url = '/opportunities/'
    permission_action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs


class OpportunityDeleteView(ObjectPermissionRequiredMixin, DeleteView):
    model = Opportunity
    template_name = 'opportunities/confirm_delete.html'
    success_url = '/opportunities/'
    permission_action = 'delete'

    def delete(self, request, *args, **kwargs):
        opp = self.get_object()
        messages.success(request, f"Opportunity '{opp.name}' deleted.")
        return super().delete(request, *args, **kwargs)


# === Forecast Dashboard ===
class ForecastDashboardView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'opportunities/forecast_dashboard.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Current forecast
        forecast_data = calculate_weighted_forecast(getattr(user, 'tenant_id', None))
        context.update(forecast_data)
        
        # Historical trend (last 30 days)
       
        today = timezone.now().date()
        trend_data = []
        for i in range(30, -1, -1):
            date = today - timedelta(days=i)
            snapshot = ForecastSnapshot.objects.filter(
                date=date,
                tenant_id=getattr(user, 'tenant_id', None)
            ).first()
            trend_data.append({
                'date': date.isoformat(),
                'forecast': float(snapshot.weighted_forecast) if snapshot else 0
            })
        context['trend_data_json'] = trend_data
        
        return context


# === Win/Loss Analysis ===
class WinLossAnalysisView(ObjectPermissionRequiredMixin, TemplateView):
    template_name = 'opportunities/win_loss_analysis.html'
    permission_action = 'read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = get_win_loss_stats(getattr(self.request.user, 'tenant_id', None))
        context.update(stats)
        return context


class WinLossAnalysisUpdateView(ObjectPermissionRequiredMixin, UpdateView):
    model = WinLossAnalysis
    form_class = WinLossAnalysisForm
    template_name = 'opportunities/win_loss_form.html'
    success_url = '/opportunities/win-loss/'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Auto-analyze if opportunity is closed
        if self.object.opportunity.stage in ['closed_won', 'closed_lost']:
            from .utils import analyze_win_loss
            analyze_win_loss(self.object.opportunity.id)
        return response


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
                    'name': opp.name,
                    'amount': opp.amount,
                    'probability': opp.probability,
                    'probability_percent': int(opp.probability * 100),
                    'close_date': opp.close_date,
                    'is_overdue': opp.close_date < today if opp.close_date else False,
                    'account': {
                        'name': opp.account.name if opp.account else 'No Account'
                    }
                })
            
            stage_total = stage_opps.aggregate(total=Sum('amount'))['total'] or 0
            
            stage_data.append({
                'id': stage.id,
                'name': stage.name,
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
            'message': f'Moved to {new_stage.name}',
            'old_stage': old_stage.name if old_stage else None,
            'new_stage': new_stage.name,
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
