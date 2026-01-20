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
        created_at__gte=one_year_ago
    ).select_related('stage')
    
    # Filter for closed opportunities (won or lost)
    opps = [o for o in opps if o.stage.is_won or o.stage.is_lost]
    
    if tenant_id:
        opps = [o for o in opps if o.tenant_id == tenant_id]
        
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
    
    for opp in opps:
        if not opp.account or opp.account.id in processed_accounts:
            continue
            
        processed_accounts.add(opp.account.id)
        
        # Get account's current engagement score
        try:
            # First try company level score if we have a way to get it
            from .utils import calculate_company_engagement_score
            score = calculate_company_engagement_score(opp.account, tenant_id=tenant_id)
        except Exception:
            # Fallback to current behavior but fix the lookup
            # Since EngagementStatus links to User, we can't directly lookup by Account
            # Let's try to get the owner's status as a proxy
            try:
                if opp.account.owner:
                    status = EngagementStatus.objects.get(account=opp.account.owner)
                    score = status.engagement_score
                else:
                    score = 0
            except EngagementStatus.DoesNotExist:
                score = 0
            
        # Get Win Rate for this account
        account_opps = Opportunity.objects.filter(account=opp.account).select_related('stage')
        closed_opps = [o for o in account_opps if o.stage.is_won or o.stage.is_lost]
        total = len(closed_opps)
        won = len([o for o in closed_opps if o.stage.is_won])
        win_rate = (won / total * 100) if total > 0 else 0
        
        data_points.append({
            'x': score, # Engagement Score
            'y': win_rate, # Win Rate %
            'name': opp.account.account_name
        })
        
    return data_points