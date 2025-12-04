from django.utils import timezone
from datetime import timedelta
from .models import Opportunity, ForecastSnapshot, WinLossAnalysis
from django.http import JsonResponse
from django.db.models import Case, When, FloatField, Sum, F, Count
from django.shortcuts import get_object_or_404
import json

def calculate_weighted_forecast(tenant_id: str = None) -> dict:
    """
    Compute total pipeline and weighted forecast.
    """
    queryset = Opportunity.objects.filter(
        stage__name__in=['prospecting', 'qualification', 'proposal', 'negotiation']
    )
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)

    # Annotate with probability
    opportunities = queryset.annotate(
        probability_value=Case(
            When(stage__name='prospecting', then=0.1),
            When(stage__name='qualification', then=0.3),
            When(stage__name='proposal', then=0.6),
            When(stage__name='negotiation', then=0.85),
            default=0.0,
            output_field=FloatField()
        )
    )

    totals = opportunities.aggregate(
        total_pipeline=Sum('amount'),
        weighted_forecast=Sum(F('amount') * F('probability_value'),output_field=FloatField()),
    )

    return {
        'total_pipeline': totals['total_pipeline'] or 0,
        'weighted_forecast': totals['weighted_forecast'] or 0,
    }


def create_forecast_snapshot(tenant_id: str = None) -> ForecastSnapshot:
    """
    Create a daily snapshot for historical reporting.
    """
    data = calculate_weighted_forecast(tenant_id)
    return ForecastSnapshot.objects.create(
        date=timezone.now().date(),
        total_pipeline_value=data['total_pipeline'],
        weighted_forecast=data['weighted_forecast'],
        tenant_id=tenant_id
    )


def analyze_win_loss(opportunity_id: int) -> WinLossAnalysis:
    """
    Create win/loss analysis for a closed opportunity.
    """
    opportunity = Opportunity.objects.get(id=opportunity_id)
    
    # Calculate sales cycle
    sales_cycle_days = (opportunity.close_date - opportunity.created_at.date()).days
    
    # Deal size category
    if opportunity.amount < 10000:
        deal_size = 'small'
    elif opportunity.amount < 100000:
        deal_size = 'medium'
    else:
        deal_size = 'large'
    
    analysis, created = WinLossAnalysis.objects.update_or_create(
        opportunity=opportunity,
        defaults={
            'is_won': opportunity.stage == 'closed_won',
            'sales_cycle_days': sales_cycle_days,
            'deal_size_category': deal_size
        }
    )
    
    return analysis


def get_win_loss_stats(tenant_id: str = None) -> dict:
    """
    Get win/loss statistics for reporting.
    """
    analyses = WinLossAnalysis.objects.all()
    if tenant_id:
        analyses = analyses.filter(tenant_id=tenant_id)
    
    total = analyses.count()
    won = analyses.filter(is_won=True).count()
    win_rate = (won / total * 100) if total > 0 else 0
    
    # Win rate by deal size
    deal_size_stats = {}
    for size in ['small', 'medium', 'large']:
        size_total = analyses.filter(deal_size_category=size).count()
        size_won = analyses.filter(deal_size_category=size, is_won=True).count()
        deal_size_stats[size] = {
            'total': size_total,
            'won': size_won,
            'win_rate': (size_won / size_total * 100) if size_total > 0 else 0
        }
    
    # Top loss reasons
    loss_reasons = analyses.filter(is_won=False).values('loss_reason').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return {
        'total_opportunities': total,
        'won_opportunities': won,
        'win_rate': round(win_rate, 1),
        'deal_size_stats': deal_size_stats,
        'top_loss_reasons': list(loss_reasons)
    }




def update_opportunity_stage(request):
    """AJAX endpoint to update opportunity stage."""
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        opp_id = data.get('opportunity_id')
        new_stage = data.get('stage')

        if new_stage not in dict(Opportunity._meta.get_field('stage').choices):
            return JsonResponse({'error': 'Invalid stage'}, status=400)

        opp = get_object_or_404(Opportunity, id=opp_id)
        # Permission check
        from core.object_permissions import OpportunityObjectPolicy
        if not OpportunityObjectPolicy.can_change(request.user, opp):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        opp.stage = new_stage
        opp.save(update_fields=['stage'])

        # Auto-create win/loss analysis if closed
        if new_stage in ['closed_won', 'closed_lost']:
            from .utils import analyze_win_loss
            analyze_win_loss(opp.id)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)