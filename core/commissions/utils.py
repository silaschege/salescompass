from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from .models import UserCommissionPlan, Commission, Quota
from opportunities.models import Opportunity

def calculate_commission(opportunity):
    """
    Calculate commission for a won opportunity based on the owner's active plan.
    Returns the calculated Commission object (unsaved) or None if no plan/rule applies.
    """
    user = opportunity.owner
    if not user:
        return None

    # Get active plan for the user
    active_plan_assignment = UserCommissionPlan.objects.filter(
        user=user,
        start_date__lte=opportunity.close_date,
        end_date__gte=opportunity.close_date
    ).first()
    
    # Fallback to open-ended plan
    if not active_plan_assignment:
         active_plan_assignment = UserCommissionPlan.objects.filter(
            user=user,
            start_date__lte=opportunity.close_date,
            end_date__isnull=True
        ).first()

    if not active_plan_assignment:
        return None

    plan = active_plan_assignment.plan
    rules = plan.rules.all()
    
    commission_amount = Decimal('0.00')
    applied_rule = None
    applied_rate = Decimal('0.00')

    # Determine Basis Amount
    basis_amount = Decimal('0.00')
    if plan.basis == 'revenue':
        basis_amount = opportunity.amount
    elif plan.basis == 'margin':
        # Assuming margin is calculated elsewhere or is a field on Opportunity
        # For now, using amount as placeholder or 20% margin assumption if not present
        # In real app, Opportunity would have 'margin' field
        basis_amount = opportunity.amount * Decimal('0.20') 
    elif plan.basis == 'units':
        # Sum quantity of products
        basis_amount = opportunity.opportunityproduct_set.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
    
    # Apply Rules
    # Logic: Find specific product rules first, then general rules
    # For simplicity in this V1, we'll apply the first matching rule based on total amount
    # A more complex engine would iterate through line items.
    
    for rule in rules:
        # Check Product Specifics (Skip for now if doing total opportunity level)
        if rule.product:
            continue # Handle line-item logic later if needed
            
        # Check Tiers
        if rule.rate_type == 'tiered':
            # Check if this opportunity falls within the tier? 
            # Or is it based on YTD sales?
            # Usually tiered is cumulative. 
            # For V1 simple implementation: Flat rate based on this deal size (Accelerator)
            if rule.tier_min_amount <= basis_amount:
                if not rule.tier_max_amount or basis_amount <= rule.tier_max_amount:
                    applied_rate = rule.rate_value
                    applied_rule = rule
                    break
        else:
            # Flat Rate
            applied_rate = rule.rate_value
            applied_rule = rule
            break
    
    if applied_rule:
        commission_amount = basis_amount * (applied_rate / 100)
        
        return Commission(
            user=user,
            opportunity=opportunity,
            amount=commission_amount,
            rate_applied=applied_rate,
            date_earned=opportunity.close_date,
            status='pending'
        )
    
    return None

def get_user_performance(user, period_start, period_end):
    """
    Get sales vs quota for a user in a period.
    """
    # Get Quota
    quota = Quota.objects.filter(
        user=user,
        period_start__lte=period_start,
        period_end__gte=period_end
    ).first()
    
    target = quota.target_amount if quota else Decimal('0.00')
    
    # Get Sales (Won Opportunities)
    # Assuming 'Won' stage is defined or is_won=True
    sales = Opportunity.objects.filter(
        owner=user,
        stage__is_won=True,
        close_date__range=[period_start, period_end]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Get Commissions
    commissions = Commission.objects.filter(
        user=user,
        date_earned__range=[period_start, period_end]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    attainment = (sales / target * 100) if target > 0 else 0
    
    return {
        'quota': target,
        'sales': sales,
        'attainment': attainment,
        'commissions_earned': commissions
    }
