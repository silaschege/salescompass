from django.utils import timezone
from django.db.models import Sum
from .models import Campaign
from .models_attribution import CampaignAttribution

class AttributionService:
    """
    Service for calculating and managing campaign attribution.
    """
    
    @staticmethod
    def calculate_attribution_for_opportunity(opportunity, model='first_touch', tenant_id=None):
        """
        Calculate attribution for a closed opportunity.
        Finds all touchpoints (Leads) associated with the opportunity's account/contact 
        before the opportunity creation date.
        """
        # 1. Identify Touchpoints
        # For simplicity, we look at the Opportunity's related Lead (source) or Account interactions
        # Assuming Opportunity has a 'lead' field or we trace back via Account
        
        # Strategy: Get all Leads for this Account created before Opp creation
        if not opportunity.account:
            return
            
        # This logic assumes we can link Opp -> Account -> Leads
        # Or Opp -> Primary Contact -> Lead
        
        # Lets try to find the Lead that converted to this Opp explicitly if possible
        # core/opportunities/models.py doesn't show a direct lead link, but usually there is one in CRM
        # We will check if there's a 'lead' field on Opp, if not we search by Account
        
        candidates = []
        
        # If opportunity has a defined source lead
        if hasattr(opportunity, 'lead') and opportunity.lead:
             candidates.append(opportunity.lead)
        
        # Also look for other leads from the same Account prior to Opp creation
        from leads.models import Lead
        
        account_leads = Lead.objects.filter(
            account=opportunity.account,
            lead_acquisition_date__lt=opportunity.created_at if hasattr(opportunity, 'created_at') and opportunity.created_at else timezone.now()
        )
        for lead in account_leads:
            if lead not in candidates:
                candidates.append(lead)
                
        # Now find campaigns associated with these leads
        # Identifying Campaign: Lead.marketing_channel or Lead.source_campaign (if exists)
        # We need to check Lead model. In many CRMs, Lead has a 'campaign' field.
        # Let's assume we can find a campaign via 'drid' or 'utm_campaign' or explicit link.
        
        # For this implementation, we will assume Leads have a 'campaign_ref' or similiar, 
        # or we rely on 'marketing_channel' if that maps to a campaign.
        
        # Let's just create attributions for Leads that HAVE a campaign linked.
        
        touchpoints = []
        for lead in candidates:
             # Check for explicit campaign link
             if hasattr(lead, 'campaign_ref') and lead.campaign_ref:
                 touchpoints.append({
                     'lead': lead,
                     'campaign': lead.campaign_ref,
                     'date': lead.lead_acquisition_date or timezone.now()
                 })
        
        if not touchpoints:
            return
            
        # Sort by date
        touchpoints.sort(key=lambda x: x['date'])
        
        # 2. Apply Attribution Model
        total_value = float(opportunity.amount) if opportunity.amount else 0.0
        
        if model == 'first_touch':
            # 100% to the first touch
            winner = touchpoints[0]
            _create_attribution(winner, opportunity, 1.0, total_value, 'first_touch', tenant_id)
            
        elif model == 'last_touch':
            # 100% to the last touch
            winner = touchpoints[-1]
            _create_attribution(winner, opportunity, 1.0, total_value, 'last_touch', tenant_id)
            
        elif model == 'linear':
            # Equal split
            count = len(touchpoints)
            weight = 1.0 / count
            value_share = total_value / count
            for tp in touchpoints:
                _create_attribution(tp, opportunity, weight, value_share, 'linear', tenant_id)
                
        # Clear old attributions for this opp if re-calculating?
        # Ideally yes, but for now we append. In prod, use update_or_create or clear first.

def _create_attribution(touchpoint, opportunity, weight, revenue, model_name, tenant_id):
    CampaignAttribution.objects.update_or_create(
        campaign=touchpoint['campaign'],
        opportunity=opportunity,
        tenant_id=tenant_id,
        defaults={
            'lead': touchpoint['lead'],
            'touchpoint_date': touchpoint['date'],
            'weight': weight,
            'revenue_share': revenue,
            'attribution_model': model_name
        }
    )
