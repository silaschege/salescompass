from django import template
from django.utils.safestring import mark_safe
from core.models import User
from leads.models import Lead
from opportunities.models import Opportunity

register = template.Library()


@register.inclusion_tag('dashboard/widgets/clv_widget.html')
def clv_widget():
    """
    Display a widget with CLV metrics
    """
    users = User.objects.all()
    
    # Calculate CLV metrics
    avg_clv = users.aggregate(avg_clv=Avg('customer_lifetime_value'))['avg_clv'] or 0
    total_clv = users.aggregate(total_clv=Sum('customer_lifetime_value'))['total_clv'] or 0
    
    context = {
        'avg_clv': avg_clv,
        'total_clv': total_clv,
    }
    
    return context


@register.inclusion_tag('dashboard/widgets/cac_widget.html')
def cac_widget():
    """
    Display a widget with CAC metrics
    """
    from marketing.models import Campaign
    from django.db.models import Sum, Count
    
    campaigns = Campaign.objects.all()
    
    # Calculate CAC metrics
    total_spend = sum([campaign.actual_cost or 0 for campaign in campaigns])
    new_customers_count = Lead.objects.filter(status='converted').count()
    
    avg_cac = 0
    if new_customers_count > 0:
        avg_cac = total_spend / new_customers_count
    
    context = {
        'avg_cac': avg_cac,
        'total_spend': total_spend,
        'new_customers_count': new_customers_count,
    }
    
    return context


@register.inclusion_tag('dashboard/widgets/sales_velocity_widget.html')
def sales_velocity_widget():
    """
    Display a widget with sales velocity metrics
    """
    opportunities = Opportunity.objects.all()
    
    # Calculate sales velocity metrics
    total_velocity = 0
    for opp in opportunities:
        total_velocity += opp.calculate_sales_velocity()
    avg_sales_velocity = total_velocity / opportunities.count() if opportunities.count() > 0 else 0
    
    # Calculate conversion rate
    total_opportunities = opportunities.count()
    won_opportunities = opportunities.filter(stage__is_won=True).count()
    conversion_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    
    context = {
        'avg_sales_velocity': avg_sales_velocity,
        'conversion_rate': conversion_rate,
    }
    
    return context


@register.inclusion_tag('dashboard/widgets/ml_win_probability_widget.html')
def ml_win_probability_widget():
    """
    Display ML-based win probability insights.
    """
    opportunities = Opportunity.objects.all()
    avg_ml_prob = opportunities.aggregate(avg_prob=Avg('probability'))['avg_prob'] or 0
    high_prob_count = opportunities.filter(probability__gt=0.7).count()
    
    return {
        'avg_ml_prob': int(avg_ml_prob * 100),
        'high_prob_count': high_prob_count,
        'total_count': opportunities.count(),
    }

@register.inclusion_tag('dashboard/widgets/ml_lead_quality_widget.html')
def ml_lead_quality_widget():
    """
    Display ML-based lead quality metrics.
    """
    leads = Lead.objects.all()
    avg_score = leads.aggregate(avg_score=Avg('lead_score'))['avg_score'] or 0
    hot_leads = leads.filter(lead_score__gt=80).count()
    
    return {
        'avg_ml_score': int(avg_score),
        'hot_leads_count': hot_leads,
        'total_leads': leads.count(),
    }


# Helper functions for metrics calculation
from django.db.models import Avg, Sum

def calculate_clv_metrics():
    """
    Calculate CLV metrics for use in views
    """
    users = User.objects.all()
    
    avg_clv = users.aggregate(avg_clv=Avg('customer_lifetime_value'))['avg_clv'] or 0
    total_clv = users.aggregate(total_clv=Sum('customer_lifetime_value'))['total_clv'] or 0
    avg_order_value = users.aggregate(avg_order=Avg('avg_order_value'))['avg_order'] or 0
    avg_purchase_frequency = users.aggregate(avg_freq=Avg('purchase_frequency'))['avg_freq'] or 0
    
    return {
        'avg_clv': avg_clv,
        'total_clv': total_clv,
        'avg_order_value': avg_order_value,
        'avg_purchase_frequency': avg_purchase_frequency,
    }


def calculate_cac_metrics():
    """
    Calculate CAC metrics for use in views
    """
    from marketing.models import Campaign
    
    campaigns = Campaign.objects.all()
    total_spend = sum([campaign.actual_cost or 0 for campaign in campaigns])
    new_customers_count = Lead.objects.filter(status='converted').count()
    
    avg_cac = 0
    if new_customers_count > 0:
        avg_cac = total_spend / new_customers_count
    
    conversion_rate = (new_customers_count / Lead.objects.count() * 100) if Lead.objects.count() > 0 else 0
    
    return {
        'avg_cac': avg_cac,
        'total_spend': total_spend,
        'new_customers_count': new_customers_count,
        'conversion_rate': conversion_rate,
    }


def calculate_sales_velocity_metrics():
    """
    Calculate sales velocity metrics for use in views
    """
    opportunities = Opportunity.objects.all()
    
    total_velocity = 0
    for opp in opportunities:
        total_velocity += opp.calculate_sales_velocity()
    avg_sales_velocity = total_velocity / opportunities.count() if opportunities.count() > 0 else 0
    
    total_opportunities = opportunities.count()
    won_opportunities = opportunities.filter(stage__is_won=True).count()
    conversion_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    
    # Calculate average sales cycle
    avg_sales_cycle = 0
    if won_opportunities > 0:
        avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in opportunities.filter(stage__is_won=True)) / won_opportunities
    else:
        open_opps = opportunities.filter(stage__is_won=False)
        if open_opps.count() > 0:
            avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in open_opps) / open_opps.count()
    
    return {
        'avg_sales_velocity': avg_sales_velocity,
        'conversion_rate': conversion_rate,
        'avg_sales_cycle': avg_sales_cycle,
    }
