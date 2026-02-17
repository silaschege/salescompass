"""
Business Intelligence Services for SalesCompass CRM
Provides data aggregation, metrics calculation, and trend analysis.
"""
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import asyncio
import logging

logger = logging.getLogger(__name__)


class DataAggregationService:
    """Aggregate data across multiple modules for BI dashboard."""
    
    def __init__(self, tenant):
        self.tenant = tenant
    
    def get_leads_summary(self, days=30):
        """Get leads summary with conversion stats."""
        from leads.models import Lead
        
        start_date = timezone.now() - timedelta(days=days)
        leads = Lead.objects.filter(tenant=self.tenant)
        
        return {
            'total': leads.count(),
            'new_this_period': leads.filter(lead_created_at__gte=start_date).count(),
            'converted': leads.filter(status='converted').count(),
            'qualified': leads.filter(status='qualified').count(),
            'by_source': list(leads.values('source').annotate(count=Count('id')).order_by('-count')[:5]),
            'by_status': list(leads.values('status').annotate(count=Count('id'))),
        }
    
    def get_opportunities_summary(self, days=30):
        """Get opportunities summary with pipeline stats."""
        from opportunities.models import Opportunity
        
        start_date = timezone.now() - timedelta(days=days)
        opps = Opportunity.objects.filter(tenant=self.tenant)
        
        return {
            'total': opps.count(),
            'total_value': opps.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'won': opps.filter(stage='closed_won').count(),
            'won_value': opps.filter(stage='closed_won').aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'by_stage': list(opps.values('stage').annotate(
                count=Count('id'),
                value=Sum('amount')
            ).order_by('stage')),
            'new_this_period': opps.filter(opportunity_created_at__gte=start_date).count(),
        }
    
    def get_accounts_summary(self):
        """Get accounts summary."""
        from accounts.models import Account
        
        accounts = Account.objects.filter(tenant=self.tenant)
        
        return {
            'total': accounts.count(),
            'active': accounts.filter(status='active').count(),
            'by_type': list(accounts.values('account_type').annotate(count=Count('id'))),
            'by_industry': list(accounts.values('industry').annotate(count=Count('id')).order_by('-count')[:5]),
        }
    
    def get_cases_summary(self, days=30):
        """Get support cases summary."""
        from cases.models import Case
        
        start_date = timezone.now() - timedelta(days=days)
        cases = Case.objects.filter(tenant=self.tenant)
        
        return {
            'total': cases.count(),
            'open': cases.filter(status__in=['new', 'in_progress']).count(),
            'resolved_this_period': cases.filter(
                status='resolved',
                case_updated_at__gte=start_date
            ).count(),
            'by_priority': list(cases.values('priority').annotate(count=Count('id'))),
            'by_status': list(cases.values('status').annotate(count=Count('id'))),
        }
    
    def get_tasks_summary(self, user=None, days=30):
        """Get tasks summary."""
        from tasks.models import Task
        
        start_date = timezone.now() - timedelta(days=days)
        tasks = Task.objects.filter(tenant=self.tenant)
        
        if user:
            tasks = tasks.filter(assigned_to=user)
        
        return {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'overdue': tasks.filter(due_date__lt=timezone.now(), status__in=['pending', 'in_progress']).count(),
            'due_today': tasks.filter(due_date__date=timezone.now().date()).count(),
            'by_priority': list(tasks.values('priority').annotate(count=Count('id'))),
        }

    def get_user_performance(self, user, days=30):
        """Get performance metrics for a specific user."""
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get user's leads
        user_leads = Lead.objects.filter(
            tenant=self.tenant,
            assigned_to=user,
            lead_created_at__gte=start_date
        )
        
        # Get user's opportunities
        user_opps = Opportunity.objects.filter(
            tenant=self.tenant,
            assigned_to=user,
            opportunity_created_at__gte=start_date
        )
        
        return {
            'user_id': user.id,
            'user_name': user.get_full_name() or user.email,
            'leads_count': user_leads.count(),
            'leads_converted': user_leads.filter(status='converted').count(),
            'opportunities_count': user_opps.count(),
            'opportunities_won': user_opps.filter(stage='closed_won').count(),
            'opportunities_value': user_opps.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        }


class MetricsCalculationService:
    """Calculate KPIs and business metrics."""
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.aggregation = DataAggregationService(tenant)
    
    def get_conversion_rate(self, days=30):
        """Calculate lead to opportunity conversion rate."""
        leads = self.aggregation.get_leads_summary(days)
        total = leads.get('total', 0)
        converted = leads.get('converted', 0)
        
        if total == 0:
            return Decimal('0')
        return Decimal(converted) / Decimal(total) * 100
    
    def get_win_rate(self, days=30):
        """Calculate opportunity win rate."""
        opps = self.aggregation.get_opportunities_summary(days)
        total = opps.get('total', 0)
        won = opps.get('won', 0)
        
        if total == 0:
            return Decimal('0')
        return Decimal(won) / Decimal(total) * 100
    
    def get_average_deal_size(self):
        """Calculate average deal size from won opportunities."""
        from opportunities.models import Opportunity
        
        result = Opportunity.objects.filter(
            tenant=self.tenant,
            stage='closed_won'
        ).aggregate(avg=Avg('amount'))
        
        return result['avg'] or Decimal('0')
    
    def get_sales_velocity(self, days=90):
        """Calculate sales velocity metric."""
        # Sales Velocity = (# Opportunities × Win Rate × Avg Deal Size) / Sales Cycle Length
        from opportunities.models import Opportunity
        
        opps = Opportunity.objects.filter(tenant=self.tenant)
        total_opps = opps.count()
        win_rate = self.get_win_rate(days) / 100
        avg_deal = self.get_average_deal_size()
        
        # Estimate sales cycle (average days from created to won)
        won_opps = opps.filter(stage='closed_won')
        if won_opps.exists():
            # Simplified - would need created_at and closed_at fields
            sales_cycle = 30  # Default 30 days
        else:
            sales_cycle = 30
        
        if sales_cycle == 0:
            return Decimal('0')
        
        return (Decimal(total_opps) * win_rate * avg_deal) / Decimal(sales_cycle)
    
    def get_all_kpis(self, days=30):
        """Get all key performance indicators."""
        return {
            'conversion_rate': round(self.get_conversion_rate(days), 1),
            'win_rate': round(self.get_win_rate(days), 1),
            'avg_deal_size': round(self.get_average_deal_size(), 2),
            'sales_velocity': round(self.get_sales_velocity(days), 2),
        }

    def get_team_performance(self, days=30):
        """Get performance metrics for the entire team."""
        from core.models import User
        
        team_members = User.objects.filter(tenant=self.tenant)
        performance_data = []
        
        for user in team_members:
            perf = self.aggregation.get_user_performance(user, days)
            performance_data.append(perf)
        
        return performance_data


class TrendAnalysisService:
    """Analyze historical trends for BI dashboard."""
    
    def __init__(self, tenant):
        self.tenant = tenant
    
    def get_leads_trend(self, days=30, interval='day'):
        """Get leads created over time."""
        from leads.models import Lead
        
        start_date = timezone.now() - timedelta(days=days)
        leads = Lead.objects.filter(
            tenant=self.tenant,
            lead_created_at__gte=start_date
        )
        
        if interval == 'week':
            trunc_func = TruncWeek
        elif interval == 'month':
            trunc_func = TruncMonth
        else:
            trunc_func = TruncDate
        
        return list(leads.annotate(
            date=trunc_func('lead_created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))
    
    def get_revenue_trend(self, days=90, interval='week'):
        """Get revenue (won opportunities) over time."""
        from opportunities.models import Opportunity
        
        start_date = timezone.now() - timedelta(days=days)
        opps = Opportunity.objects.filter(
            tenant=self.tenant,
            stage='closed_won',
            opportunity_created_at__gte=start_date
        )
        
        if interval == 'week':
            trunc_func = TruncWeek
        elif interval == 'month':
            trunc_func = TruncMonth
        else:
            trunc_func = TruncDate
        
        return list(opps.annotate(
            date=trunc_func('opportunity_created_at')
        ).values('date').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date'))
    
    def get_pipeline_funnel(self):
        """Get pipeline funnel data for visualization."""
        from opportunities.models import Opportunity
        
        stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        funnel_data = []
        
        opps = Opportunity.objects.filter(tenant=self.tenant)
        
        for stage in stages:
            count = opps.filter(stage=stage).count()
            value = opps.filter(stage=stage).aggregate(total=Sum('amount'))['total'] or 0
            funnel_data.append({
                'stage': stage.replace('_', ' ').title(),
                'count': count,
                'value': float(value)
            })
        
        return funnel_data
    
    def get_conversion_trend(self, days=90):
        """Get lead to opportunity conversion trend over time."""
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get leads by week
        leads = Lead.objects.filter(
            tenant=self.tenant,
            lead_created_at__gte=start_date
        ).annotate(
            week=TruncWeek('lead_created_at')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')
        
        # Get opportunities by week
        opps = Opportunity.objects.filter(
            tenant=self.tenant,
            opportunity_created_at__gte=start_date
        ).annotate(
            week=TruncWeek('opportunity_created_at')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')
        
        # Combine data
        trend_data = {}
        for lead in leads:
            week = lead['week'].strftime('%Y-%m-%d')
            trend_data[week] = {'leads': lead['count'], 'opportunities': 0}
            
        for opp in opps:
            week = opp['week'].strftime('%Y-%m-%d')
            if week in trend_data:
                trend_data[week]['opportunities'] = opp['count']
            else:
                trend_data[week] = {'leads': 0, 'opportunities': opp['count']}
        
        # Calculate conversion rates
        result = []
        for week, data in trend_data.items():
            conversion_rate = 0
            if data['leads'] > 0:
                conversion_rate = round((data['opportunities'] / data['leads']) * 100, 2)
                
            result.append({
                'week': week,
                'leads': data['leads'],
                'opportunities': data['opportunities'],
                'conversion_rate': conversion_rate
            })
        
        return sorted(result, key=lambda x: x['week'])

    def get_user_trend(self, user, days=30, interval='day'):
        """Get user-specific performance trend."""
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        start_date = timezone.now() - timedelta(days=days)
        
        if interval == 'week':
            trunc_func = TruncWeek
        elif interval == 'month':
            trunc_func = TruncMonth
        else:
            trunc_func = TruncDate
        
        # Get user's leads
        leads = Lead.objects.filter(
            tenant=self.tenant,
            assigned_to=user,
            lead_created_at__gte=start_date
        ).annotate(
            date=trunc_func('lead_created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Get user's opportunities
        opps = Opportunity.objects.filter(
            tenant=self.tenant,
            assigned_to=user,
            opportunity_created_at__gte=start_date
        ).annotate(
            date=trunc_func('opportunity_created_at')
        ).values('date').annotate(
            count=Count('id'),
            total_value=Sum('amount')
        ).order_by('date')
        
        return {
            'leads_trend': list(leads),
            'opportunities_trend': list(opps)
        }


class RealTimeProcessor:
    """Process real-time data updates for BI dashboard."""
    
    def __init__(self, tenant):
        self.tenant = tenant
    
    def get_live_metrics(self):
        """Get real-time metrics snapshot."""
        aggregation = DataAggregationService(self.tenant)
        metrics = MetricsCalculationService(self.tenant)
        
        return {
            'timestamp': timezone.now().isoformat(),
            'leads': aggregation.get_leads_summary(7),
            'opportunities': aggregation.get_opportunities_summary(7),
            'kpis': metrics.get_all_kpis(30),
        }
    
    def get_activity_feed(self, limit=10):
        """Get recent activity across all modules."""
        from audit_logs.models import AuditLog
        
        logs = AuditLog.objects.filter(
            tenant=self.tenant
        ).select_related('user').order_by('-audit_log_created_at')[:limit]
        
        return [{
            'action': log.action,
            'resource': log.resource_name,
            'user': log.user.get_full_name() if log.user else 'System',
            'timestamp': log.audit_log_created_at.isoformat(),
        } for log in logs]
    
    def get_streaming_data(self, last_timestamp=None):
        """
        Get streaming data updates since last timestamp.
        This method is optimized for WebSocket connections.
        """
        from audit_logs.models import AuditLog
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        # If no timestamp provided, get last 5 minutes
        if not last_timestamp:
            last_timestamp = timezone.now() - timedelta(minutes=5)
        else:
            # Parse the ISO format timestamp
            try:
                last_timestamp = timezone.datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            except ValueError:
                last_timestamp = timezone.now() - timedelta(minutes=5)
        
        # Get recent activities
        recent_activities = AuditLog.objects.filter(
            tenant=self.tenant,
            audit_log_created_at__gt=last_timestamp
        ).select_related('user').order_by('-audit_log_created_at')[:5]
        
        # Get recent leads
        recent_leads = Lead.objects.filter(
            tenant=self.tenant,
            lead_created_at__gt=last_timestamp
        ).order_by('-lead_created_at')[:5]
        
        # Get recent opportunities
        recent_opps = Opportunity.objects.filter(
            tenant=self.tenant,
            opportunity_created_at__gt=last_timestamp
        ).order_by('-opportunity_created_at')[:5]
        
        return {
            'timestamp': timezone.now().isoformat(),
            'activities': [{
                'id': log.id,
                'action': log.action,
                'resource': log.resource_name,
                'user': log.user.get_full_name() if log.user else 'System',
                'timestamp': log.audit_log_created_at.isoformat(),
            } for log in recent_activities],
            'leads': [{
                'id': lead.id,
                'name': str(lead),
                'source': lead.source,
                'status': lead.status,
                'created_at': lead.lead_created_at.isoformat(),
            } for lead in recent_leads],
            'opportunities': [{
                'id': opp.id,
                'name': str(opp),
                'stage': opp.stage,
                'amount': float(opp.amount or 0),
                'created_at': opp.opportunity_created_at.isoformat(),
            } for opp in recent_opps]
        }

    def get_user_notifications(self, user):
        """Get notifications for a specific user."""
        from core.models import Notification
        
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        return [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.isoformat(),
            'is_read': n.is_read
        } for n in notifications]


class AdvancedVisualizationService:
    """Generate data for advanced visualizations."""
    
    def __init__(self, tenant):
        self.tenant = tenant
    
    def get_heatmap_data(self, days=30):
        """Generate heatmap data showing activity by day/hour."""
        from audit_logs.models import AuditLog
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get activity grouped by day of week and hour
        heatmap_data = AuditLog.objects.filter(
            tenant=self.tenant,
            audit_log_created_at__gte=start_date
        ).extra(select={
            'day_of_week': 'EXTRACT(dow FROM audit_log_created_at)',
            'hour_of_day': 'EXTRACT(hour FROM audit_log_created_at)'
        }).values('day_of_week', 'hour_of_day').annotate(
            count=Count('id')
        )
        
        # Convert to matrix format
        matrix = [[0 for _ in range(24)] for _ in range(7)]
        for entry in heatmap_data:
            day = int(entry['day_of_week'])
            hour = int(entry['hour_of_day'])
            count = entry['count']
            matrix[day][hour] = count
            
        return {
            'matrix': matrix,
            'labels': {
                'days': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'hours': list(range(24))
            }
        }
    
    def get_forecast_data(self, days=90):
        """Generate forecast data based on historical trends."""
        from opportunities.models import Opportunity
        import random
        
        # Get historical data
        start_date = timezone.now() - timedelta(days=days)
        historical_data = Opportunity.objects.filter(
            tenant=self.tenant,
            stage='closed_won',
            opportunity_created_at__gte=start_date
        ).annotate(
            date=TruncDate('opportunity_created_at')
        ).values('date').annotate(
            amount=Sum('amount')
        ).order_by('date')
        
        # Simple forecasting algorithm (in a real implementation, this would use ML)
        # For now, we'll generate sample forecast data
        forecast_points = []
        actual_points = []
        
        # Process historical data
        for point in historical_data:
            actual_points.append({
                'date': point['date'].isoformat(),
                'amount': float(point['amount'] or 0)
            })
        
        # Generate forecast (simple linear projection with randomness)
        if actual_points:
            last_actual = actual_points[-1]
            last_amount = last_actual['amount']
            
            # Generate next 30 days of forecast
            for i in range(1, 31):
                forecast_date = timezone.now().date() + timedelta(days=i)
                # Add some randomness to make it realistic
                growth_factor = 1 + random.uniform(-0.1, 0.2)  # -10% to +20% variation
                forecast_amount = last_amount * growth_factor
                
                forecast_points.append({
                    'date': forecast_date.isoformat(),
                    'amount': max(0, forecast_amount)  # Ensure non-negative
                })
        
        return {
            'historical': actual_points[-30:],  # Last 30 days of actual data
            'forecast': forecast_points
        }
    
    def get_comparative_analysis(self, metric='revenue', period1_start=None, period1_end=None, 
                               period2_start=None, period2_end=None):
        """Compare metrics between two periods."""
        from opportunities.models import Opportunity
        from leads.models import Lead
        
        if not all([period1_start, period1_end, period2_start, period2_end]):
            # Default to month-over-month comparison
            today = timezone.now().date()
            period2_end = today
            period2_start = today - timedelta(days=30)
            period1_end = period2_start - timedelta(days=1)
            period1_start = period1_end - timedelta(days=30)
        
        # Convert to datetime
        period1_start = timezone.datetime.combine(period1_start, timezone.datetime.min.time())
        period1_end = timezone.datetime.combine(period1_end, timezone.datetime.max.time())
        period2_start = timezone.datetime.combine(period2_start, timezone.datetime.min.time())
        period2_end = timezone.datetime.combine(period2_end, timezone.datetime.max.time())
        
        if metric == 'revenue':
            # Compare revenue between periods
            period1_data = Opportunity.objects.filter(
                tenant=self.tenant,
                stage='closed_won',
                opportunity_created_at__range=(period1_start, period1_end)
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            period2_data = Opportunity.objects.filter(
                tenant=self.tenant,
                stage='closed_won',
                opportunity_created_at__range=(period2_start, period2_end)
            ).aggregate(total=Sum('amount'))['total'] or 0
            
        elif metric == 'leads':
            # Compare leads between periods
            period1_data = Lead.objects.filter(
                tenant=self.tenant,
                lead_created_at__range=(period1_start, period1_end)
            ).count()
            
            period2_data = Lead.objects.filter(
                tenant=self.tenant,
                lead_created_at__range=(period2_start, period2_end)
            ).count()
        
        # Calculate percentage change
        if period1_data > 0:
            change_percent = ((period2_data - period1_data) / period1_data) * 100
        else:
            change_percent = 100 if period2_data > 0 else 0
            
        return {
            'metric': metric,
            'period1': {
                'start': period1_start.date().isoformat(),
                'end': period1_end.date().isoformat(),
                'value': float(period1_data)
            },
            'period2': {
                'start': period2_start.date().isoformat(),
                'end': period2_end.date().isoformat(),
                'value': float(period2_data)
            },
            'change': {
                'absolute': float(period2_data - period1_data),
                'percentage': round(change_percent, 2)
            }
        }

    def get_geographic_data(self):
        """Get geographic distribution of leads/customers."""
        from accounts.models import Account
        
        # Group accounts by country/city
        geo_data = Account.objects.filter(tenant=self.tenant).values(
            'billing_country', 'billing_city'
        ).annotate(
            count=Count('id'),
            total_value=Sum('annual_revenue')
        ).order_by('-count')
        
        return list(geo_data)

    def get_cohort_analysis(self, months=12):
        """Perform cohort analysis on customer acquisition."""
        from accounts.models import Account
        
        # Get accounts created in the last N months
        start_date = timezone.now() - timedelta(days=months*30)
        accounts = Account.objects.filter(
            tenant=self.tenant,
            account_created_at__gte=start_date
        ).annotate(
            cohort_month=TruncMonth('account_created_at')
        ).values('cohort_month').annotate(
            count=Count('id')
        ).order_by('cohort_month')
        
        return list(accounts)
    



# """
# Business Intelligence Services for SalesCompass CRM
# Provides data aggregation, metrics calculation, and trend analysis.
# """
# from django.db.models import Count, Sum, Avg, F, Q
# from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, ExtractWeekDay, ExtractHour
# from django.utils import timezone
# from datetime import timedelta
# from decimal import Decimal
# from django.core.cache import cache
# import logging
# import functools

# logger = logging.getLogger(__name__)

# def cache_data(timeout=300):
#     """Decorator to cache service method results based on tenant and args."""
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(self, *args, **kwargs):
#             # Generate cache key based on method name, tenant, and arguments
#             key_parts = [self.tenant.id, func.__name__]
#             key_parts.extend([str(a) for a in args])
#             key_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
#             cache_key = f"bi_cache:{':'.join(map(str, key_parts))}"
            
#             result = cache.get(cache_key)
#             if result is not None:
#                 return result
            
#             result = func(self, *args, **kwargs)
#             cache.set(cache_key, result, timeout)
#             return result
#         return wrapper
#     return decorator

# class DataAggregationService:
#     def __init__(self, tenant):
#         self.tenant = tenant
    
#     @cache_data(timeout=300)
#     def get_leads_summary(self, days=30):
#         from leads.models import Lead
#         start_date = timezone.now() - timedelta(days=days)
#         leads = Lead.objects.filter(tenant=self.tenant)
        
#         return {
#             'total': leads.count(),
#             'new_this_period': leads.filter(lead_created_at__gte=start_date).count(),
#             'converted': leads.filter(status='converted').count(),
#             'by_source': list(leads.values('source').annotate(count=Count('id')).order_by('-count')[:5]),
#         }
    
#     @cache_data(timeout=300)
#     def get_opportunities_summary(self, days=30):
#         from opportunities.models import Opportunity
#         start_date = timezone.now() - timedelta(days=days)
#         opps = Opportunity.objects.filter(tenant=self.tenant)
        
#         total_val = opps.aggregate(total=Sum('amount'))['total'] or Decimal('0')
#         won_val = opps.filter(stage='closed_won').aggregate(total=Sum('amount'))['total'] or Decimal('0')

#         return {
#             'total': opps.count(),
#             'total_value': float(total_val),
#             'won': opps.filter(stage='closed_won').count(),
#             'won_value': float(won_val),
#             'new_this_period': opps.filter(opportunity_created_at__gte=start_date).count(),
#         }

#     # ... (Other summary methods would follow the same pattern) ...

# class TrendAnalysisService:
#     def __init__(self, tenant):
#         self.tenant = tenant
    
#     @cache_data(timeout=600) # Cache trends longer (10 mins)
#     def get_revenue_trend(self, days=90, interval='week'):
#         from opportunities.models import Opportunity
#         start_date = timezone.now() - timedelta(days=days)
        
#         trunc_func = TruncWeek if interval == 'week' else TruncMonth
        
#         data = Opportunity.objects.filter(
#             tenant=self.tenant,
#             stage='closed_won',
#             opportunity_created_at__gte=start_date
#         ).annotate(
#             date=trunc_func('opportunity_created_at')
#         ).values('date').annotate(
#             total=Sum('amount')
#         ).order_by('date')
        
#         # Format for Chart.js
#         return [{
#             'date': item['date'].strftime('%Y-%m-%d'), 
#             'total': float(item['total'] or 0)
#         } for item in data]

#     @cache_data(timeout=600)
#     def get_pipeline_funnel(self):
#         from opportunities.models import Opportunity
#         stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won']
        
#         data = []
#         for stage in stages:
#             count = Opportunity.objects.filter(tenant=self.tenant, stage=stage).count()
#             data.append({
#                 'stage': stage.replace('_', ' ').title(),
#                 'count': count
#             })
#         return data

# class AdvancedVisualizationService:
#     def __init__(self, tenant):
#         self.tenant = tenant

#     @cache_data(timeout=3600) # Cache expensive heatmap for 1 hour
#     def get_heatmap_data(self, days=30):
#         """Generate heatmap data showing activity by day/hour."""
#         from audit_logs.models import AuditLog
#         start_date = timezone.now() - timedelta(days=days)
        
#         # Efficient DB grouping
#         heatmap_data = AuditLog.objects.filter(
#             tenant=self.tenant,
#             audit_log_created_at__gte=start_date
#         ).annotate(
#             day=ExtractWeekDay('audit_log_created_at'), # 1=Sunday, 7=Saturday
#             hour=ExtractHour('audit_log_created_at')
#         ).values('day', 'hour').annotate(count=Count('id'))
        
#         # Initialize 7x24 matrix (0-6 days, 0-23 hours)
#         # Python lists are 0-indexed, Django ExtractWeekDay is 1-indexed (Sunday=1)
#         matrix = [[0 for _ in range(24)] for _ in range(7)]
        
#         for entry in heatmap_data:
#             # Convert 1-7 to 0-6
#             day_idx = (entry['day'] - 1) % 7 
#             hour_idx = entry['hour']
#             matrix[day_idx][hour_idx] = entry['count']
            
#         return {
#             'matrix': matrix,
#             'days': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
#             'hours': [f"{h}:00" for h in range(24)]
#         }

