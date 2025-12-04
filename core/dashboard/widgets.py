"""
Dashboard Widget System
Base classes and core widgets for the Dashboard Builder.
"""
from abc import ABC, abstractmethod
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
from .query_builder import get_widget_data


class BaseWidget(ABC):
    """
    Abstract base class for dashboard widgets.
    All widgets must inherit from this and implement get_context_data.
    """
    # Class attributes to be overridden
    widget_type = None
    name = None
    description = None
    template_path = None
    default_span = 6  # Bootstrap grid span (1-12)
    required_permission = None
    
    def __init__(self, request, settings=None):
        self.request = request
        self.user = request.user
        self.tenant_id = getattr(request.user, 'tenant_id', None)
        self.settings = settings or {}
    
    @abstractmethod
    def get_context_data(self):
        """
        Return context dict for widget rendering.
        Must be implemented by all widget subclasses.
        """
        pass
    
    def has_permission(self):
        """Check if user has permission to view this widget."""
        if not self.required_permission:
            return True
        return self.user.has_perm(self.required_permission)
    
    def get_date_range(self):
        """Get date range from settings or use defaults."""
        range_type = self.settings.get('date_range', '30_days')
        
        if range_type == '7_days':
            start_date = timezone.now() - timedelta(days=7)
        elif range_type == '30_days':
            start_date = timezone.now() - timedelta(days=30)
        elif range_type == '90_days':
            start_date = timezone.now() - timedelta(days=90)
        elif range_type == 'this_month':
            start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        elif range_type == 'this_quarter':
            current_month = timezone.now().month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1
            start_date = timezone.now().replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0)
        else:
            start_date = timezone.now() - timedelta(days=30)
        
        return start_date, timezone.now()


class RevenueWidget(BaseWidget):
    """Revenue metrics widget showing won opportunities."""
    widget_type = 'revenue'
    name = 'Revenue Chart'
    description = 'Shows revenue from won opportunities'
    template_path = 'dashboard/widgets/revenue.html'
    default_span = 6
    
    def get_context_data(self):
        from opportunities.models import Opportunity
        
        start_date, end_date = self.get_date_range()
        
        # Get won opportunities in date range
        won_opps = Opportunity.objects.filter(
            tenant_id=self.tenant_id,
            stage__is_won=True,
            close_date__gte=start_date,
            close_date__lte=end_date
        )
        
        total_revenue = won_opps.aggregate(total=Sum('amount'))['total'] or 0
        opp_count = won_opps.count()
        
        # Calculate average deal size
        avg_deal_size = total_revenue / opp_count if opp_count > 0 else 0
        
        return {
            'widget_type': self.widget_type,
            'total_revenue': total_revenue,
            'opportunity_count': opp_count,
            'average_deal_size': avg_deal_size,
            'date_range': self.settings.get('date_range', '30_days'),
        }


class PipelineWidget(BaseWidget):
    """Sales pipeline widget showing opportunities by stage."""
    widget_type = 'pipeline'
    name = 'Sales Pipeline'
    description = 'Shows opportunities grouped by stage'
    template_path = 'dashboard/widgets/pipeline.html'
    default_span = 6
    
    def get_context_data(self):
        from opportunities.models import Opportunity, OpportunityStage
        
        # Get active stages
        stages = OpportunityStage.objects.filter(
            tenant_id=self.tenant_id,
            is_active=True
        ).order_by('order')
        
        # Get pipeline value by stage
        pipeline_data = []
        total_pipeline = 0
        
        for stage in stages:
            opps = Opportunity.objects.filter(
                tenant_id=self.tenant_id,
                stage=stage
            )
            stage_value = opps.aggregate(total=Sum('amount'))['total'] or 0
            stage_count = opps.count()
            
            pipeline_data.append({
                'stage': stage.name,
                'value': stage_value,
                'count': stage_count,
                'color': stage.color,
            })
            total_pipeline += stage_value
        
        return {
            'widget_type': self.widget_type,
            'pipeline_data': pipeline_data,
            'total_pipeline': total_pipeline,
        }


class TasksWidget(BaseWidget):
    """Task list widget showing user's tasks."""
    widget_type = 'tasks'
    name = 'My Tasks'
    description = 'Shows assigned tasks'
    template_path = 'dashboard/widgets/tasks.html'
    default_span = 4
    
    def get_context_data(self):
        # Check for dynamic configuration
        if self.settings.get('model'):
            # Use dynamic query builder
            widget_data = get_widget_data(self.settings, self.tenant_id)
            return {
                'widget_type': self.widget_type,
                'dynamic_data': widget_data,
                'is_dynamic': True,
            }

        # Default implementation
        from tasks.models import Task
        
        # Get user's tasks
        user_tasks = Task.objects.filter(
            tenant_id=self.tenant_id,
            assigned_to=self.user
        ).exclude(
            status_ref__name='completed'
        ).order_by('due_date')[:10]
        
        # Count by status
        total_tasks = user_tasks.count()
        overdue_count = user_tasks.filter(due_date__lt=timezone.now()).count()
        today_count = user_tasks.filter(
            due_date__date=timezone.now().date()
        ).count()
        
        return {
            'widget_type': self.widget_type,
            'tasks': user_tasks,
            'total_tasks': total_tasks,
            'overdue_count': overdue_count,
            'today_count': today_count,
            'is_dynamic': False,
        }


class LeadsWidget(BaseWidget):
    """Lead metrics widget."""
    widget_type = 'leads'
    name = 'Lead Metrics'
    description = 'Shows lead statistics and conversion rates'
    template_path = 'dashboard/widgets/leads.html'
    default_span = 4
    
    def get_context_data(self):
        from leads.models import Lead
        
        start_date, end_date = self.get_date_range()
        
        # Get leads in date range
        leads = Lead.objects.filter(
            tenant_id=self.tenant_id,
            created_at__gte=start_date
        )
        
        total_leads = leads.count()
        qualified_leads = leads.filter(status_ref__name='qualified').count()
        converted_leads = leads.filter(
            status_ref__name='converted',
            converted_at__gte=start_date
        ).count()
        
        # Calculate conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Group by source
        by_source = []
        from leads.models import LeadSource
        sources = LeadSource.objects.filter(tenant_id=self.tenant_id, is_active=True)
        
        for source in sources:
            count = leads.filter(source_ref=source).count()
            if count > 0:
                by_source.append({
                    'source': source.label,
                    'count': count,
                    'icon': source.icon,
                })
        
        return {
            'widget_type': self.widget_type,
            'total_leads': total_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'conversion_rate': round(conversion_rate, 1),
            'by_source': by_source,
        }



class NPSWidget(BaseWidget):
    """NPS Score widget."""
    widget_type = 'nps'
    name = 'NPS Score'
    description = 'Shows Net Promoter Score'
    template_path = 'dashboard/widgets/nps.html'
    default_span = 4
    
    def get_context_data(self):
        # Mock implementation if NPS app not fully ready or use simple query
        try:
            from nps.models import NPSResponse
            responses = NPSResponse.objects.filter(tenant_id=self.tenant_id)
            # Calculate NPS
            promoters = responses.filter(score__gte=9).count()
            detractors = responses.filter(score__lte=6).count()
            total = responses.count()
            
            nps_score = ((promoters - detractors) / total * 100) if total > 0 else 0
        except ImportError:
            nps_score = 0
            total = 0
            
        return {
            'widget_type': self.widget_type,
            'nps_score': round(nps_score),
            'total_responses': total,
        }


class CasesWidget(BaseWidget):
    """Support cases widget."""
    widget_type = 'cases'
    name = 'Support Cases'
    description = 'Shows open cases by priority'
    template_path = 'dashboard/widgets/cases.html'
    default_span = 4
    
    def get_context_data(self):
        from cases.models import Case
        
        open_cases = Case.objects.filter(
            tenant_id=self.tenant_id,
            status__in=['new', 'in_progress']
        )
        
        by_priority = []
        for priority in ['critical', 'high', 'medium', 'low']:
            count = open_cases.filter(priority=priority).count()
            if count > 0:
                by_priority.append({'priority': priority, 'count': count})
                
        return {
            'widget_type': self.widget_type,
            'total_open': open_cases.count(),
            'by_priority': by_priority,
        }


class ActivityWidget(BaseWidget):
    """Recent activity widget."""
    widget_type = 'activity'
    name = 'Recent Activity'
    description = 'Shows recent system activity'
    template_path = 'dashboard/widgets/activity.html'
    default_span = 6
    
    def get_context_data(self):
        # This would ideally query an AuditLog or ActivityStream model
        # For now, we'll aggregate from core models as done in MainDashboardView
        activities = []
        
        # We can reuse logic or just show a placeholder if too complex to duplicate
        # Let's try to fetch a few items
        from leads.models import Lead
        from opportunities.models import Opportunity
        
        recent_leads = Lead.objects.filter(tenant_id=self.tenant_id).order_by('-created_at')[:5]
        for lead in recent_leads:
            activities.append({
                'icon': 'user-plus',
                'text': f"New lead: {lead.full_name}",
                'time': lead.created_at
            })
            
        recent_opps = Opportunity.objects.filter(tenant_id=self.tenant_id).order_by('-created_at')[:5]
        for opp in recent_opps:
            activities.append({
                'icon': 'dollar-sign',
                'text': f"New opportunity: {opp.name}",
                'time': opp.created_at
            })
            
        activities.sort(key=lambda x: x['time'], reverse=True)
        
        return {
            'widget_type': self.widget_type,
            'activities': activities[:10]
        }


class LeaderboardWidget(BaseWidget):
    """Sales leaderboard widget."""
    widget_type = 'leaderboard'
    name = 'Sales Leaderboard'
    description = 'Top sales representatives'
    template_path = 'dashboard/widgets/leaderboard.html'
    default_span = 6
    
    def get_context_data(self):
        from sales.models import Sale
        from core.models import User
        
        start_date, _ = self.get_date_range()
        
        # Aggregate sales by user
        # This is a simplified version
        leaders = []
        users = User.objects.filter(tenant_id=self.tenant_id, is_active=True)
        
        for user in users:
            revenue = Sale.objects.filter(
                account__owner=user,
                sale_date__gte=start_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            if revenue > 0:
                leaders.append({
                    'name': user.get_full_name() or user.email,
                    'revenue': revenue,
                    'avatar': user.avatar.url if hasattr(user, 'avatar') and user.avatar else None
                })
                
        leaders.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'widget_type': self.widget_type,
            'leaders': leaders[:5]
        }





def get_widget(widget_type, request, settings=None):
    """Factory function to instantiate widgets."""
    widget_class = WIDGET_REGISTRY.get(widget_type)
    if not widget_class:
        raise ValueError(f"Unknown widget type: {widget_type}")
    return widget_class(request, settings)

class AccountsWidget(BaseWidget):
    """Accounts overview widget."""
    widget_type = 'accounts'
    name = 'Accounts Overview'
    description = 'Shows account health and status'
    template_path = 'dashboard/widgets/accounts.html'
    default_span = 6
    required_permission = 'accounts.view_account'
    
    def get_context_data(self):
        # Check for dynamic configuration
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from accounts.models import Account
        
        accounts = Account.objects.filter(tenant_id=self.tenant_id)
        total_accounts = accounts.count()
        active_accounts = accounts.filter(status='active').count()
        at_risk = accounts.filter(health_score__lt=40, status='active').count()
        
        return {
            'widget_type': self.widget_type,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'at_risk_accounts': at_risk,
            'is_dynamic': False,
        }


class InfrastructureWidget(BaseWidget):
    """Infrastructure usage widget."""
    widget_type = 'infrastructure'
    name = 'Infrastructure Usage'
    description = 'Shows server and resource usage'
    template_path = 'dashboard/widgets/infrastructure.html'
    default_span = 6
    required_permission = 'infrastructure.view_server'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        # Mock data or simple query
        return {
            'widget_type': self.widget_type,
            'server_count': 5,
            'avg_cpu_usage': 45,
            'avg_memory_usage': 60,
            'is_dynamic': False,
        }


class TenantsWidget(BaseWidget):
    """Tenant management widget."""
    widget_type = 'tenants'
    name = 'Tenant Management'
    description = 'Shows tenant statistics'
    template_path = 'dashboard/widgets/tenants.html'
    default_span = 6
    required_permission = 'tenants.view_tenant'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        # Mock data
        return {
            'widget_type': self.widget_type,
            'total_tenants': 12,
            'active_tenants': 10,
            'trial_tenants': 2,
            'is_dynamic': False,
        }


class MarketingWidget(BaseWidget):
    """Marketing campaigns widget."""
    widget_type = 'marketing'
    name = 'Marketing Campaigns'
    description = 'Shows campaign performance'
    template_path = 'dashboard/widgets/marketing.html'
    default_span = 6
    required_permission = 'marketing.view_campaign'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        return {
            'widget_type': self.widget_type,
            'active_campaigns': 3,
            'total_emails_sent': 1500,
            'open_rate': 25.5,
            'is_dynamic': False,
        }


class AutomationWidget(BaseWidget):
    """Automation workflows widget."""
    widget_type = 'automation'
    name = 'Automation Workflows'
    description = 'Shows workflow execution stats'
    template_path = 'dashboard/widgets/automation.html'
    default_span = 6
    required_permission = 'automation.view_workflow'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        return {
            'widget_type': self.widget_type,
            'active_workflows': 8,
            'executions_today': 145,
            'failed_executions': 2,
            'is_dynamic': False,
        }




class OpportunitiesWidget(BaseWidget):
    """Opportunities overview widget."""
    widget_type = 'opportunities'
    name = 'Opportunities Overview'
    description = 'Shows opportunity pipeline and metrics'
    template_path = 'dashboard/widgets/opportunities.html'
    default_span = 6
    required_permission = 'opportunities.view_opportunity'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from opportunities.models import Opportunity
        
        opps = Opportunity.objects.filter(tenant_id=self.tenant_id)
        open_opps = opps.exclude(stage__is_won=True).exclude(stage__is_lost=True)
        
        return {
            'widget_type': self.widget_type,
            'total_opportunities': open_opps.count(),
            'total_value': open_opps.aggregate(total=Sum('amount'))['total'] or 0,
            'won_this_month': opps.filter(stage__is_won=True, close_date__gte=timezone.now().replace(day=1)).count(),
            'is_dynamic': False,
        }


class SalesWidget(BaseWidget):
    """Sales performance widget."""
    widget_type = 'sales'
    name = 'Sales Performance'
    description = 'Shows sales metrics and revenue'
    template_path = 'dashboard/widgets/sales.html'
    default_span = 6
    required_permission = 'sales.view_sale'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from sales.models import Sale
        
        start_date, _ = self.get_date_range()
        sales = Sale.objects.filter(sale_date__gte=start_date)
        
        return {
            'widget_type': self.widget_type,
            'total_sales': sales.count(),
            'total_revenue': sales.aggregate(total=Sum('amount'))['total'] or 0,
            'is_dynamic': False,
        }


class ProductsWidget(BaseWidget):
    """Products metrics widget."""
    widget_type = 'products'
    name = 'Product Metrics'
    description = 'Shows product performance and inventory'
    template_path = 'dashboard/widgets/products.html'
    default_span = 4
    required_permission = 'products.view_product'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        from products.models import Product
        
        products = Product.objects.filter(tenant_id=self.tenant_id)
        
        return {
            'widget_type': self.widget_type,
            'total_products': products.count(),
            'active_products': products.filter(is_active=True).count(),
            'is_dynamic': False,
        }


class ProposalsWidget(BaseWidget):
    """Proposals pipeline widget."""
    widget_type = 'proposals'
    name = 'Proposal Pipeline'
    description = 'Shows proposal status and metrics'
    template_path = 'dashboard/widgets/proposals.html'
    default_span = 6
    required_permission = 'proposals.view_proposal'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from proposals.models import Proposal
        
        proposals = Proposal.objects.filter(tenant_id=self.tenant_id)
        
        return {
            'widget_type': self.widget_type,
            'total_proposals': proposals.count(),
            'pending_proposals': proposals.filter(status='draft').count(),
            'accepted_proposals': proposals.filter(status='accepted').count(),
            'is_dynamic': False,
        }


class CommunicationWidget(BaseWidget):
    """Communication stats widget."""
    widget_type = 'communication'
    name = 'Communication Stats'
    description = 'Shows email and call activity'
    template_path = 'dashboard/widgets/communication.html'
    default_span = 4
    required_permission = 'communication.view_email'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'emails_sent': 125,
            'calls_made': 48,
            'is_dynamic': False,
        }


class EngagementWidget(BaseWidget):
    """Engagement metrics widget."""
    widget_type = 'engagement'
    name = 'Engagement Metrics'
    description = 'Shows customer engagement scores'
    template_path = 'dashboard/widgets/engagement.html'
    default_span = 4
    required_permission = 'engagement.view_engagementevent'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from engagement.models import EngagementEvent
        
        start_date, _ = self.get_date_range()
        events = EngagementEvent.objects.filter(
            tenant_id=self.tenant_id,
            timestamp__gte=start_date
        )
        
        return {
            'widget_type': self.widget_type,
            'total_events': events.count(),
            'unique_accounts': events.values('account').distinct().count(),
            'is_dynamic': False,
        }


class ReportsWidget(BaseWidget):
    """Reports dashboard widget."""
    widget_type = 'reports'
    name = 'Report Dashboard'
    description = 'Shows saved reports and analytics'
    template_path = 'dashboard/widgets/reports.html'
    default_span = 6
    required_permission = 'reports.view_report'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
            
        from reports.models import Report
        
        reports = Report.objects.filter(created_by=self.user)
        
        return {
            'widget_type': self.widget_type,
            'total_reports': reports.count(),
            'recent_reports': reports.order_by('-created_at')[:5],
            'is_dynamic': False,
        }


class CommissionsWidget(BaseWidget):
    """Commission tracking widget."""
    widget_type = 'commissions'
    name = 'Commission Tracking'
    description = 'Shows commission earnings and status'
    template_path = 'dashboard/widgets/commissions.html'
    default_span = 4
    required_permission = 'sales.view_commission'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'total_earned': 5420,
            'pending_payout': 1200,
            'is_dynamic': False,
        }


class LearnWidget(BaseWidget):
    """Learning progress widget."""
    widget_type = 'learn'
    name = 'Learning Progress'
    description = 'Shows training and course progress'
    template_path = 'dashboard/widgets/learn.html'
    default_span = 4
    required_permission = 'learn.view_course'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'courses_enrolled': 3,
            'courses_completed': 1,
            'is_dynamic': False,
        }


class DeveloperWidget(BaseWidget):
    """Developer tools widget."""
    widget_type = 'developer'
    name = 'Developer Tools'
    description = 'Shows API usage and webhooks'
    template_path = 'dashboard/widgets/developer.html'
    default_span = 6
    required_permission = 'settings_app.view_apikey'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'api_calls_today': 1247,
            'active_webhooks': 5,
            'is_dynamic': False,
        }


class BillingWidget(BaseWidget):
    """Billing overview widget."""
    widget_type = 'billing'
    name = 'Billing Overview'
    description = 'Shows subscription and payment status'
    template_path = 'dashboard/widgets/billing.html'
    default_span = 6
    required_permission = 'billing.view_subscription'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'mrr': 2500,
            'active_subscriptions': 12,
            'is_dynamic': False,
        }


class SettingsWidget(BaseWidget):
    """System settings widget."""
    widget_type = 'settings'
    name = 'System Settings'
    description = 'Shows system configuration status'
    template_path = 'dashboard/widgets/settings.html'
    default_span = 4
    required_permission = 'settings_app.view_tenantsettings'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'pending_updates': 2,
            'system_health': 'Good',
            'is_dynamic': False,
        }


class AuditLogsWidget(BaseWidget):
    """Audit logs widget."""
    widget_type = 'audit_logs'
    name = 'Audit Logs'
    description = 'Shows recent system activity'
    template_path = 'dashboard/widgets/audit_logs.html'
    default_span = 6
    required_permission = 'audit_logs.view_auditlog'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'events_today': 342,
            'critical_events': 0,
            'is_dynamic': False,
        }


class FeatureFlagsWidget(BaseWidget):
    """Feature flags widget."""
    widget_type = 'feature_flags'
    name = 'Feature Flags'
    description = 'Shows feature flag status'
    template_path = 'dashboard/widgets/feature_flags.html'
    default_span = 4
    required_permission = 'feature_flags.view_featureflag'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'total_flags': 15,
            'enabled_flags': 8,
            'is_dynamic': False,
        }


class GlobalAlertsWidget(BaseWidget):
    """Global alerts widget."""
    widget_type = 'global_alerts'
    name = 'Global Alerts'
    description = 'Shows system-wide alerts'
    template_path = 'dashboard/widgets/global_alerts.html'
    default_span = 6
    required_permission = 'global_alerts.view_globalalert'
    
    def get_context_data(self):
        if self.settings.get('model'):
            return {
                'widget_type': self.widget_type,
                'dynamic_data': get_widget_data(self.settings, self.tenant_id),
                'is_dynamic': True,
            }
        
        return {
            'widget_type': self.widget_type,
            'active_alerts': 1,
            'resolved_today': 3,
            'is_dynamic': False,
        }


# Widget Registry - must be at end after all widget classes are defined
WIDGET_REGISTRY = {
    "revenue": RevenueWidget,
    "pipeline": PipelineWidget,
    "tasks": TasksWidget,
    "leads": LeadsWidget,
    "nps": NPSWidget,
    "cases": CasesWidget,
    "activity": ActivityWidget,
    "leaderboard": LeaderboardWidget,
    "accounts": AccountsWidget,
    "infrastructure": InfrastructureWidget,
    "tenants": TenantsWidget,
    "marketing": MarketingWidget,
    "automation": AutomationWidget,
    "opportunities": OpportunitiesWidget,
    "sales": SalesWidget,
    "products": ProductsWidget,
    "proposals": ProposalsWidget,
    "communication": CommunicationWidget,
    "engagement": EngagementWidget,
    "reports": ReportsWidget,
    "commissions": CommissionsWidget,
    "learn": LearnWidget,
    "developer": DeveloperWidget,
    "billing": BillingWidget,
    "settings": SettingsWidget,
    "audit_logs": AuditLogsWidget,
    "feature_flags": FeatureFlagsWidget,
    "global_alerts": GlobalAlertsWidget,
}

