"""
Workflow Analytics Service for SalesCompass CRM

Provides analytics and metrics for workflow executions:
- Execution success rates
- Performance metrics (execution time)
- Trend analysis
- Per-workflow and tenant-wide analytics

Usage:
    from automation.analytics import analytics_service
    
    # Get metrics for a specific workflow
    metrics = analytics_service.get_workflow_metrics(workflow_id=1)
    
    # Get tenant-wide analytics
    stats = analytics_service.get_tenant_analytics(tenant_id='tenant-123')
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Min, Max, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

logger = logging.getLogger(__name__)


class WorkflowAnalyticsService:
    """
    Service for computing and caching workflow analytics.
    """
    
    def get_workflow_metrics(
        self,
        workflow_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            start_date: Start of date range (defaults to 30 days ago)
            end_date: End of date range (defaults to now)
        
        Returns:
            Dictionary with execution metrics
        """
        from .models import WorkflowExecution, Workflow
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        try:
            workflow = Workflow.objects.get(id=workflow_id)
        except Workflow.DoesNotExist:
            return {'error': 'Workflow not found'}
        
        executions = WorkflowExecution.objects.filter(
            workflow_id=workflow_id,
            workflow_execution_executed_at__gte=start_date,
            workflow_execution_executed_at__lte=end_date,
        )
        
        total = executions.count()
        completed = executions.filter(workflow_execution_status='completed').count()
        failed = executions.filter(workflow_execution_status='failed').count()
        pending = executions.filter(workflow_execution_status__in=['pending', 'running']).count()
        
        # Performance metrics (only completed executions)
        perf_metrics = executions.filter(
            workflow_execution_status='completed',
            workflow_execution_execution_time_ms__isnull=False
        ).aggregate(
            avg_time=Avg('workflow_execution_execution_time_ms'),
            min_time=Min('workflow_execution_execution_time_ms'),
            max_time=Max('workflow_execution_execution_time_ms'),
        )
        
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'workflow_id': workflow_id,
            'workflow_name': workflow.workflow_name,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'executions': {
                'total': total,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'success_rate': round(success_rate, 2),
            },
            'performance': {
                'avg_execution_time_ms': round(perf_metrics['avg_time'] or 0, 2),
                'min_execution_time_ms': perf_metrics['min_time'] or 0,
                'max_execution_time_ms': perf_metrics['max_time'] or 0,
            }
        }
    
    def get_tenant_analytics(
        self,
        tenant_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for all workflows in a tenant.
        
        Args:
            tenant_id: Tenant identifier
            start_date: Start of date range
            end_date: End of date range
        
        Returns:
            Dictionary with tenant-wide analytics
        """
        from .models import WorkflowExecution, Workflow
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Get all workflows for tenant
        workflows = Workflow.objects.filter(tenant_id=tenant_id)
        workflow_count = workflows.count()
        active_workflows = workflows.filter(workflow_is_active=True).count()
        
        # Execution stats
        executions = WorkflowExecution.objects.filter(
            workflow__tenant_id=tenant_id,
            workflow_execution_executed_at__gte=start_date,
            workflow_execution_executed_at__lte=end_date,
        )
        
        total_executions = executions.count()
        status_breakdown = executions.values('workflow_execution_status').annotate(
            count=Count('id')
        )
        
        # Top performing workflows
        top_workflows = executions.filter(
            workflow_execution_status='completed'
        ).values('workflow__workflow_name', 'workflow_id').annotate(
            execution_count=Count('id'),
            avg_time=Avg('workflow_execution_execution_time_ms')
        ).order_by('-execution_count')[:5]
        
        return {
            'tenant_id': tenant_id,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'workflows': {
                'total': workflow_count,
                'active': active_workflows,
            },
            'executions': {
                'total': total_executions,
                'by_status': {item['workflow_execution_status']: item['count'] for item in status_breakdown},
            },
            'top_workflows': list(top_workflows),
        }
    
    def get_execution_trends(
        self,
        tenant_id: str = None,
        workflow_id: int = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get daily execution trends.
        
        Args:
            tenant_id: Filter by tenant
            workflow_id: Filter by specific workflow
            days: Number of days to look back
        
        Returns:
            List of daily execution counts
        """
        from .models import WorkflowExecution
        
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = WorkflowExecution.objects.filter(
            workflow_execution_executed_at__gte=start_date
        )
        
        if tenant_id:
            queryset = queryset.filter(workflow__tenant_id=tenant_id)
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        
        daily_stats = queryset.annotate(
            date=TruncDate('workflow_execution_executed_at')
        ).values('date').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(workflow_execution_status='completed')),
            failed=Count('id', filter=Q(workflow_execution_status='failed')),
        ).order_by('date')
        
        return list(daily_stats)
    
    def get_action_type_stats(
        self,
        tenant_id: str = None,
        days: int = 30,
    ) -> Dict[str, int]:
        """
        Get execution counts by action type.
        
        Args:
            tenant_id: Filter by tenant
            days: Number of days to look back
        
        Returns:
            Dictionary of action type counts
        """
        from .models import WorkflowAction
        
        queryset = WorkflowAction.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(workflow__tenant_id=tenant_id)
        
        action_counts = queryset.values('workflow_action_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {item['workflow_action_type']: item['count'] for item in action_counts}
    
    def update_analytics_snapshot(
        self,
        workflow_id: int = None,
        tenant_id: str = None,
        snapshot_date: datetime = None,
    ) -> None:
        """
        Update or create analytics snapshot for caching.
        
        Args:
            workflow_id: Specific workflow (or None for tenant-wide)
            tenant_id: Tenant identifier
            snapshot_date: Date for snapshot (defaults to yesterday)
        """
        from .models import WorkflowAnalyticsSnapshot, WorkflowExecution
        
        if not snapshot_date:
            snapshot_date = (timezone.now() - timedelta(days=1)).date()
        
        start = timezone.make_aware(datetime.combine(snapshot_date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(snapshot_date, datetime.max.time()))
        
        queryset = WorkflowExecution.objects.filter(
            workflow_execution_executed_at__gte=start,
            workflow_execution_executed_at__lte=end,
        )
        
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        if tenant_id:
            queryset = queryset.filter(workflow__tenant_id=tenant_id)
        
        total = queryset.count()
        successful = queryset.filter(workflow_execution_status='completed').count()
        failed = queryset.filter(workflow_execution_status='failed').count()
        
        perf = queryset.filter(
            workflow_execution_execution_time_ms__isnull=False
        ).aggregate(
            avg=Avg('workflow_execution_execution_time_ms'),
            min=Min('workflow_execution_execution_time_ms'),
            max=Max('workflow_execution_execution_time_ms'),
        )
        
        # Get or create snapshot
        snapshot, created = WorkflowAnalyticsSnapshot.objects.update_or_create(
            workflow_id=workflow_id,
            snapshot_date=snapshot_date,
            tenant_id=tenant_id,
            defaults={
                'total_executions': total,
                'successful_executions': successful,
                'failed_executions': failed,
                'avg_execution_time_ms': perf['avg'] or 0,
                'min_execution_time_ms': perf['min'] or 0,
                'max_execution_time_ms': perf['max'] or 0,
            }
        )
        
        logger.info(f"{'Created' if created else 'Updated'} analytics snapshot for {snapshot_date}")


# Singleton instance
analytics_service = WorkflowAnalyticsService()
