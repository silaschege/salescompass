from django.db.models import Avg, Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from opportunities.models import Opportunity
from .models import EngagementStatus, EngagementEvent

def calculate_engagement_roi(tenant_id=None):
    """
    Calculate correlation between engagement scores and opportunity outcomes.
    Returns data for a scatter plot: X=Engagement Score, Y=Win Rate % (or Deal Value)
    """
    # Filter opportunities closed in last year
    one_year_ago = timezone.now() - timedelta(days=365)
    
    # Get all closed opportunities
    opps = Opportunity.objects.filter(
        created_at__gte=one_year_ago,
        status__in=['closed_won', 'closed_lost'] 
    )
    
    if tenant_id:
        opps = opps.filter(tenant_id=tenant_id)
        
    # We need to map Opportunity -> Account -> EngagementStatus
    # But historical engagement score at the time of closure isn't stored in EngagementStatus (it's current).
    # Ideally we'd use a snapshot. For MVP, we'll use current Engagement Score of the account 
    # as a proxy (assuming high engagement is sustained).
    
    # Or better: Average engagement score of the account
    
    data_points = []
    
    # Group by account to get (Avg Score, Win Rate)
    # This is heavy, optimization: use aggregates if possible. 
    # Python loop is fine for MVP volume.
    
    processed_accounts = set()
    
    for opp in opps.select_related('account'):
        if not opp.account or opp.account.id in processed_accounts:
            continue
            
        processed_accounts.add(opp.account.id)
        
        # Get account's current engagement score
        try:
            status = EngagementStatus.objects.get(account=opp.account)
            score = status.engagement_score
        except EngagementStatus.DoesNotExist:
            score = 0
            
        # Get Win Rate for this account
        account_opps = Opportunity.objects.filter(account=opp.account, status__in=['closed_won', 'closed_lost'])
        total = account_opps.count()
        won = account_opps.filter(status='closed_won').count()
        win_rate = (won / total * 100) if total > 0 else 0
        
        data_points.append({
            'x': score, # Engagement Score
            'y': win_rate, # Win Rate %
            'name': opp.account.name
        })
        
    return data_points
