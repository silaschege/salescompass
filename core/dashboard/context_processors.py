from dashboard.models import DashboardConfig

def user_dashboards(request):
    """
    Add user's custom dashboards to template context.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Get user's dashboards, ordered by default first, then by updated date
        dashboards = DashboardConfig.objects.filter(
            user=request.user
        ).order_by('-is_default', '-config_updated_at')[:10]  # Limit to 10 most recent
        
        context['user_dashboards'] = dashboards
    
    return context
