from django.db.models import Sum, F
from django.db import models
from django.utils import timezone
from .models import Project, ProjectMilestone, TimesheetEntry

def get_project_profitability(project):
    """
    Calculates profitability for a given project.
    Revenue = Billable hours * Billing rate + Milestone billing amounts
    Cost = Hours * Cost rate
    """
    # 1. Milestone Revenue
    milestone_revenue = project.milestones.filter(
        is_completed=True, 
        is_billable=True
    ).aggregate(total=Sum('billing_amount'))['total'] or 0

    # 2. Timesheet Revenue & Cost
    time_data = project.timesheet_entries.filter(
        timesheet__status='approved'
    ).aggregate(
        total_revenue=Sum(F('hours') * F('billing_rate'), filter=F('is_billable')),
        total_cost=Sum(F('hours') * F('cost_rate'))
    )

    timesheet_revenue = time_data['total_revenue'] or 0
    total_cost = time_data['total_cost'] or 0

    total_revenue = milestone_revenue + timesheet_revenue
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'profit': profit,
        'margin': margin,
        'milestone_revenue': milestone_revenue,
        'timesheet_revenue': timesheet_revenue,
    }

def get_tenant_projects_profitability(tenant):
    """
    Returns profitability data for all projects in a tenant.
    """
    projects = Project.objects.filter(tenant=tenant)
    results = []
    for project in projects:
        profitability = get_project_profitability(project)
        results.append({
            'project': project,
            'data': profitability
        })
    return results

def get_resource_capacity(tenant):
    """
    Calculates resource utilization for all staff in a tenant.
    Utilization = (Sum of hours allocated / Standard 40h week) * 100
    """
    from core.models import User
    users = User.objects.filter(tenant=tenant)
    results = []
    
    for user in users:
        # Get active allocations
        allocations = user.project_allocations.filter(
            tenant=tenant,
            start_date__lte=timezone.now().date(),
        ).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now().date()))
        
        total_allocation_pct = allocations.aggregate(total=Sum('allocation_percentage'))['total'] or 0
        
        results.append({
            'user': user,
            'total_allocation_percentage': total_allocation_pct,
            'is_over_capacity': total_allocation_pct > 100,
            'allocations': allocations
        })
    return results

def get_revenue_recognition(tenant):
    """
    Summarizes recognized revenue for a tenant.
    Recognized Revenue = (Completed Milestones billing) + (Approved Timesheet billable revenue)
    """
    projects = Project.objects.filter(tenant=tenant)
    results = []
    
    for project in projects:
        profitability = get_project_profitability(project)
        results.append({
            'project': project,
            'recognized_revenue': profitability['total_revenue'],
            'milestone_portion': profitability['milestone_revenue'],
            'timesheet_portion': profitability['timesheet_revenue'],
        })
    return results
