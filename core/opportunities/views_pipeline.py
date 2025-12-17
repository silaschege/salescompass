from django.views.generic import TemplateView
from core.permissions import ObjectPermissionRequiredMixin
from django.db.models import Sum
from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


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
