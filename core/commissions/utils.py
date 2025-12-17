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

    plan = active_plan_assignment.assigned_plan
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

def calculate_forecast(user, start_date=None, end_date=None):
    """
    Calculate forecasted commission based on open opportunities.
    """
    if not start_date:
        start_date = timezone.now().date()
    if not end_date:
        # Default to end of month/quarter? Let's say end of current month for now
        today = timezone.now().date()
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timezone.timedelta(days=1)

    # Get Open Opportunities
    # Assuming standard stages like 'Prospecting', 'Qualification', 'Proposal', 'Negotiation' are not won/lost
    # We need to filter by close_date in the period
    open_opportunities = Opportunity.objects.filter(
        owner=user,
        stage__is_won=False,
        stage__is_lost=False,
        close_date__range=[start_date, end_date]
    )

    forecast_amount = Decimal('0.00')
    weighted_forecast_amount = Decimal('0.00')

    # Reuse logic? We need a way to DRY this up.
    # ideally we refactor calculate_commission to take an opportunity and return amount without saving.
    # Refactoring calculate_commission to be split into 'compute' and 'save' parts would be best.
    # For now, we'll traverse and compute.

    for opp in open_opportunities:
        # Temporary "Commission" object just to get the amount
        # We need to mock the object or use a helper
        
        # Helper call
        # We need to know the rule that WOULD apply.
        # This duplicates logic from calculate_commission.
        # Let's EXTRACT the rule finding logic.
        
        # ... For this iteration, I will copy the logic for speed, but note a refactor is needed.
        commission_obj = calculate_commission(opp)
        
        if commission_obj:
            potential_comm = commission_obj.amount
            forecast_amount += potential_comm
            
            # Weighted
            probability = Decimal(opp.probability or 0)
            weighted_forecast_amount += potential_comm * probability

    return {
        'forecast_amount': forecast_amount,
        'weighted_forecast_amount': weighted_forecast_amount,
        'opportunity_count': open_opportunities.count()
    }

def generate_payment_records(user, period_end):
    """
    Generate a payment record for unpaid commissions up to period_end.
    """
    from .models import CommissionPayment
    
    unpaid_commissions = Commission.objects.filter(
        user=user,
        status__in=['approved', 'pending'], # Depending on policy, maybe only approved?
        date_earned__lte=period_end,
        payment_record__isnull=True # Not already paid
    )
    
    if not unpaid_commissions.exists():
        return None
        
    total_amount = unpaid_commissions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Create Payment Record
    # We need a start date. Maybe the earliest commission date?
    earliest_date = unpaid_commissions.order_by('date_earned').first().date_earned
    tenant = unpaid_commissions.first().tenant
    
    payment = CommissionPayment.objects.create(
        user=user,
        tenant=tenant,
        period_start=earliest_date,
        period_end=period_end,
        total_amount=total_amount,
        status='calculated'
    )
    
    # Link commissions
    unpaid_commissions.update(payment_record=payment, status='processing')
    
    return payment
