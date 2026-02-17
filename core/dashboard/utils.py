"""
Utility functions for dashboard data aggregation and formatting.
"""
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import json

from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from cases.models import Case
from sales.models import Sale


def get_revenue_chart_data(user, timeframe='6m'):
    """
    Get revenue chart data for the specified timeframe.
    
    Args:
        user: User object to filter data for
        timeframe: String like '30d', '6m', '12m' (default: '6m')
    
    Returns:
        dict: {'labels': [...], 'data': [...]}
    """
    now = timezone.now()
    
    # Parse timeframe
    if timeframe == '30d':
        num_periods = 30
        period_type = 'day'
    elif timeframe == '12m':
        num_periods = 12
        period_type = 'month'
    else:  # Default to 6m
        num_periods = 6
        period_type = 'month'
    
    labels = []
    data = []
    
    for i in range(num_periods - 1, -1, -1):
        if period_type == 'day':
            period_date = now - timedelta(days=i)
            period_start = period_date.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            label = period_date.strftime('%m/%d')
        else:  # month
            period_date = now - timedelta(days=30*i)
            period_start = period_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (period_start + timedelta(days=32)).replace(day=1)
            period_end = next_month
            label = period_start.strftime('%b')
        
        revenue = Sale.objects.filter(
            sale_date__gte=period_start,
            sale_date__lt=period_end
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        labels.append(label)
        data.append(float(revenue))
    
    return {
        'labels': json.dumps(labels),
        'data': json.dumps(data)
    }


def get_pipeline_snapshot(user):
    """
    Get pipeline snapshot data grouped by stage.
    
    Args:
        user: User object to filter data for
    
    Returns:
        dict: {'labels': [...], 'data': [...]}
    """
    # Get user's opportunities
    opps_qs = Opportunity.objects.for_user(user) if hasattr(Opportunity.objects, 'for_user') else Opportunity.objects.filter(owner=user)
    open_opps = opps_qs.exclude(stage__is_won=True).exclude(stage__is_lost=True)
    
    labels = []
    data = []
    
    # Get all opportunity stages
    stages = OpportunityStage.objects.filter(is_won=False, is_lost=False).order_by('order')
    
    for stage in stages:
        count = open_opps.filter(stage=stage).count()
        if count > 0:
            labels.append(stage.name)
            data.append(count)
    
    return {
        'labels': json.dumps(labels),
        'data': json.dumps(data)
    }


def get_activity_feed(user, limit=10):
    """
    Get recent activity feed combining Leads, Opportunities, and Cases.
    
    Args:
        user: User object to filter data for
        limit: Maximum number of activities to return (default: 10)
    
    Returns:
        list: List of activity dicts with type, title, description, timestamp
    """
    activities = []
    
    # Get user-filtered querysets
    leads_qs = Lead.objects.for_user(user) if hasattr(Lead.objects, 'for_user') else Lead.objects.filter(owner=user)
    opps_qs = Opportunity.objects.for_user(user) if hasattr(Opportunity.objects, 'for_user') else Opportunity.objects.filter(owner=user)
    cases_qs = Case.objects.for_user(user) if hasattr(Case.objects, 'for_user') else Case.objects.filter(owner=user)
    
    # Recent leads (limit to avoid too many queries)
    recent_leads = leads_qs.order_by('-created_at')[:limit // 3 + 1]
    for lead in recent_leads:
        activities.append({
            'type': 'lead',
            'title': f'New Lead: {lead.full_name}',
            'description': f'{lead.company} - {lead.get_industry_display()}',
            'timestamp': lead.created_at
        })
    
    # Recent opportunities
    recent_opps = opps_qs.order_by('-created_at')[:limit // 3 + 1]
    for opp in recent_opps:
        activities.append({
            'type': 'opportunity',
            'title': f'Opportunity: {opp.name}',
            'description': f'${opp.amount:,.0f} - {opp.stage.name}',
            'timestamp': opp.created_at
        })
    
    # Recent cases
    recent_cases = cases_qs.order_by('-created_at')[:limit // 3 + 1]
    for case in recent_cases:
        activities.append({
            'type': 'case',
            'title': f'Case: {case.subject}',
            'description': f'{case.get_priority_display()} priority - {case.get_status_display()}',
            'timestamp': case.created_at
        })
    
    # Sort by timestamp and limit
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]


def calculate_percentage_change(current, previous):
    """
    Calculate percentage change between two values.
    
    Args:
        current: Current value
        previous: Previous value
    
    Returns:
        int: Percentage change
    """
    if previous == 0:
        return 100 if current > 0 else 0
    return int(((current - previous) / previous) * 100)
