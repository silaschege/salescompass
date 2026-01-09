from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from .models import Sale, SalesPerformanceMetric
from opportunities.models import Opportunity
from core.models import User
from tenants.models import TenantTerritory

def calculate_sales_metrics(start_date, end_date, user_id=None, tenant_id=None):
    """
    Calculate sales performance metrics for a given period.
    Returns a dictionary of metrics.
    """
    # Base filter
    sales_filter = Q(sale_date__date__gte=start_date, sale_date__date__lte=end_date)
    opp_filter = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
    
    if tenant_id:
        sales_filter &= Q(sales_rep__tenant_id=tenant_id)
        opp_filter &= Q(tenant_id=tenant_id)
        
    if user_id:
        sales_filter &= Q(sales_rep_id=user_id)
        opp_filter &= Q(owner_id=user_id)
    
    # Revenue & Deals
    sales_data = Sale.objects.filter(sales_filter).aggregate(
        total_revenue=Sum('amount'),
        total_deals=Count('id'),
        avg_deal_size=Avg('amount')
    )
    
    total_revenue = sales_data['total_revenue'] or 0
    total_deals = sales_data['total_deals'] or 0
    avg_deal_size = sales_data['avg_deal_size'] or 0
    
    # Opportunities & Win Rate
    # Note: Using Opportunity logic - won stages usually defined in model or settings
    # Assuming 'closed_won' is a stage identifier or we check is_won boolean
    opps = Opportunity.objects.filter(opp_filter)
    total_opps = opps.count()
    won_opps = opps.filter(stage__is_won=True).count()
    lost_opps = opps.filter(stage__is_lost=True).count()
    
    win_rate = 0.0
    if (won_opps + lost_opps) > 0:
        win_rate = (won_opps / (won_opps + lost_opps)) * 100
    
    # Sales Cycle (Average days to close for WON opportunities in period)
    cycle_days = []
    for opp in opps.filter(stage__is_won=True):
        if opp.closed_date and opp.created_at:
            # Check if closed_date is date or datetime
            closed = opp.closed_date
            created = opp.created_at.date() if hasattr(opp.created_at, 'date') else opp.created_at
            days = (closed - created).days
            if days >= 0:
                cycle_days.append(days)
    
    avg_sales_cycle = sum(cycle_days) / len(cycle_days) if cycle_days else 0
    
    return {
        'total_revenue': float(total_revenue),
        'total_deals': total_deals,
        'avg_deal_size': float(avg_deal_size),
        'win_rate': float(win_rate),
        'avg_sales_cycle': float(avg_sales_cycle),
        'start_date': start_date,
        'end_date': end_date
    }

def aggregate_and_store_metrics(date=None):
    """
    Run daily aggregation and store in SalesPerformanceMetric.
    Typically run via celery task.
    """
    from tenants.models import Tenant
    if not date:
        date = timezone.now().date()
        
    for tenant in Tenant.objects.all():
        # Aggregate for Organization (All)
        org_metrics = calculate_sales_metrics(date, date, tenant_id=tenant.id)
        _create_metric_snapshot(date, 'revenue', org_metrics['total_revenue'], 'organization', tenant=tenant)
        _create_metric_snapshot(date, 'win_rate', org_metrics['win_rate'], 'organization', tenant=tenant)
        
        # Aggregate per User (Active Sales Reps in current tenant)
        users = User.objects.filter(is_active=True, tenant_id=tenant.id)
        for user in users:
            user_metrics = calculate_sales_metrics(date, date, user_id=user.id, tenant_id=tenant.id)
            if user_metrics['total_revenue'] > 0 or user_metrics['total_deals'] > 0: # Store only if activity
                _create_metric_snapshot(date, 'revenue', user_metrics['total_revenue'], 'user', user.id, tenant=tenant)
                _create_metric_snapshot(date, 'win_rate', user_metrics['win_rate'], 'user', user.id, tenant=tenant)

def _create_metric_snapshot(date, name, value, dimension, dimension_id=None, tenant=None):
    if not tenant:
        return
        
    SalesPerformanceMetric.objects.update_or_create(
        tenant=tenant,
        date=date,
        metric_name=name,
        dimension=dimension,
        dimension_id=dimension_id,
        defaults={'value': value}
    )
