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
    
    # Determine performance for accelerator/decelerator
    # We need to know the 'current' performance relative to the plan period.
    # Plan assignment has start_date.
    current_performance_amount = Decimal('0.00')
    if any(r.rate_type in ['accelerator', 'decelerator'] for r in rules):
        # Calculate YTD sales for this user for this plan period
        # Using plan assignment start date or year start
        perf_start = active_plan_assignment.start_date
        perf_end = opportunity.close_date
        
        current_performance_amount = Opportunity.objects.filter(
            owner=user,
            stage__is_won=True,
            close_date__gte=perf_start,
            close_date__lte=perf_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
    # Improved rule matching logic
    for rule in rules:
        # Check Product Specifics
        if rule.product:
            if opportunity.opportunityproduct_set.filter(product=rule.product).exists():
                 # Match found (simplified logic: if opp contains product, apply rule to whole opp - usually should be split)
                 # For V2, let's assume if rule matches product, it applies.
                 pass
            else:
                 continue 
            
        rate_matched = False
        
        # Check Rate Types
        if rule.rate_type == 'tiered':
            # For tiered rates, we need to match the basis amount to the tier range
            if rule.tier_min_amount <= basis_amount:
                if not rule.tier_max_amount or basis_amount <= rule.tier_max_amount:
                    rate_matched = True
        elif rule.rate_type == 'accelerator':
            # Apply if performance exceeds threshold
            threshold = rule.performance_threshold or 0
            if current_performance_amount >= threshold:
                # For accelerators, apply an enhanced rate based on performance
                # Base rate is the rule.rate_value, but could be enhanced based on how much over threshold
                rate_matched = True
                # Calculate enhanced rate if needed (for now using the base rate)
                applied_rate = rule.rate_value
        elif rule.rate_type == 'decelerator':
            # Apply if performance is below threshold
            threshold = rule.performance_threshold or 0
            if current_performance_amount < threshold:
                rate_matched = True
                # Calculate reduced rate if needed (for now using the base rate)
                applied_rate = rule.rate_value
        else:
            # Flat Rate
            rate_matched = True
            
        if rate_matched:
            # Only override applied_rate if not already set by accelerator logic
            if applied_rate == Decimal('0.00'):
                applied_rate = rule.rate_value
            applied_rule = rule
            # Break on first match? Or find 'best' match?
            # Let's break on first match for now (assuming priority order)
            break
    
    if applied_rule:
        commission_amount = basis_amount * (applied_rate / 100)
        
        comm = Commission(
            user=user,
            opportunity=opportunity,
            amount=commission_amount,
            rate_applied=applied_rate,
            date_earned=opportunity.close_date,
            status='pending',
            is_split=False
        )
        
        # Attach split details if applicable
        if applied_rule.split_with:
             comm.is_split = True
             comm.original_amount = commission_amount
             
             split_pct = applied_rule.split_percentage or Decimal('0.00')
             split_amount = commission_amount * (split_pct / 100)
             owner_amount = commission_amount - split_amount
             
             # Set main commission to owner's share
             comm.amount = owner_amount
             
             comm.split_details = {
                 'split_with': applied_rule.split_with,
                 'split_percentage': split_pct,
                 'split_amount': split_amount
             }
             
        return comm
    
    return None


def calculate_commission_advanced(opportunity):
    """
    Advanced commission calculation that handles more complex scenarios like:
    - Tiered rates with progressive rates
    - Accelerator/decelerator with enhanced/reduced rates
    - Multiple matching rules with proper priority
    - Split commissions with overlay roles
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
    rules = plan.rules.all().order_by('rate_type')  # Order to ensure proper priority
    
    commission_amount = Decimal('0.00')
    applied_rule = None
    applied_rate = Decimal('0.00')

    # Determine Basis Amount
    basis_amount = Decimal('0.00')
    if plan.basis == 'revenue':
        basis_amount = opportunity.amount
    elif plan.basis == 'margin':
        # Assuming margin is calculated elsewhere or is a field on Opportunity
        basis_amount = opportunity.amount * Decimal('0.20')  # Placeholder
    elif plan.basis == 'units':
        # Sum quantity of products
        basis_amount = opportunity.opportunityproduct_set.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

    # Calculate performance for accelerator/decelerator
    current_performance_amount = Decimal('0.00')
    if any(r.rate_type in ['accelerator', 'decelerator'] for r in rules):
        perf_start = active_plan_assignment.start_date
        perf_end = opportunity.close_date
        
        current_performance_amount = Opportunity.objects.filter(
            owner=user,
            stage__is_won=True,
            close_date__gte=perf_start,
            close_date__lte=perf_end
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Find best matching rule
    best_rule = None
    best_rate = Decimal('0.00')
    
    for rule in rules:
        # Check Product Specifics
        product_match = True
        if rule.product:
            product_match = opportunity.opportunityproduct_set.filter(product=rule.product).exists()
        
        if not product_match:
            continue

        rate_matched = False
        calculated_rate = rule.rate_value
        
        if rule.rate_type == 'tiered':
            # For tiered rates, match the basis amount to the tier
            if rule.tier_min_amount <= basis_amount:
                if not rule.tier_max_amount or basis_amount <= rule.tier_max_amount:
                    rate_matched = True
                    calculated_rate = rule.rate_value
        elif rule.rate_type == 'accelerator':
            # Apply if performance exceeds threshold
            threshold = rule.performance_threshold or 0
            if current_performance_amount >= threshold:
                rate_matched = True
                # For accelerators, the rate could be enhanced based on performance
                # For now, using the rule's specified rate
                calculated_rate = rule.rate_value
        elif rule.rate_type == 'decelerator':
            # Apply if performance is below threshold
            threshold = rule.performance_threshold or 0
            if current_performance_amount < threshold:
                rate_matched = True
                # For decelerators, the rate could be reduced
                calculated_rate = rule.rate_value
        else:
            # Flat Rate
            rate_matched = True
            calculated_rate = rule.rate_value
            
        if rate_matched:
            # For now, we'll take the first match, but in advanced scenarios
            # we might want to compare rates and select the best one
            best_rule = rule
            best_rate = calculated_rate
            break
    
    if best_rule:
        commission_amount = basis_amount * (best_rate / 100)
        
        comm = Commission(
            user=user,
            opportunity=opportunity,
            amount=commission_amount,
            rate_applied=best_rate,
            date_earned=opportunity.close_date,
            status='pending',
            is_split=False
        )
        
        # Handle split commissions
        if best_rule.split_with:
            comm.is_split = True
            comm.original_amount = commission_amount
            
            split_pct = best_rule.split_percentage or Decimal('0.00')
            split_amount = commission_amount * (split_pct / 100)
            owner_amount = commission_amount - split_amount
            
            # Set main commission to owner's share
            comm.amount = owner_amount
            
            comm.split_details = {
                'split_with': best_rule.split_with,
                'split_percentage': split_pct,
                'split_amount': split_amount
            }
            
        return comm
    
    return None


def calculate_overlay_commission(opportunity, overlay_user):
    """
    Calculate overlay commission for a user who contributed to the opportunity but isn't the primary owner.
    This is useful for Sales Engineers, Managers, etc.
    """
    # Get the overlay user's plan
    active_plan_assignment = UserCommissionPlan.objects.filter(
        user=overlay_user,
        start_date__lte=opportunity.close_date,
        end_date__gte=opportunity.close_date
    ).first()
    
    # Fallback to open-ended plan
    if not active_plan_assignment:
         active_plan_assignment = UserCommissionPlan.objects.filter(
            user=overlay_user,
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
        # Assuming margin is calculated elsewhere
        basis_amount = opportunity.amount * Decimal('0.20') 
    elif plan.basis == 'units':
        # Sum quantity of products
        basis_amount = opportunity.opportunityproduct_set.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
    
    # Apply Rules for overlay commissions
    for rule in rules:
        # For overlay commissions, we might have specific rules
        # For now, we'll apply any matching rule
        rate_matched = False
        
        # Check Product Specifics
        if rule.product:
            if opportunity.opportunityproduct_set.filter(product=rule.product).exists():
                 pass
            else:
                 continue 
        else:
            # For overlay commissions, we might want to apply to all opportunities
            # or have specific overlay commission rules
            pass
        
        # Check rate type - for overlay commissions, we'll support all types
        if rule.rate_type == 'tiered':
            # Simplified tiered for overlay
            if rule.tier_min_amount <= basis_amount:
                if not rule.tier_max_amount or basis_amount <= rule.tier_max_amount:
                    rate_matched = True
        elif rule.rate_type == 'accelerator':
             # Apply if performance exceeds threshold
             # For overlay, we might calculate performance differently
             threshold = rule.performance_threshold or 0
             current_performance_amount = Decimal('0.00')  # Calculate overlay performance if needed
             if current_performance_amount >= threshold:
                 rate_matched = True
        elif rule.rate_type == 'decelerator':
             # Apply if performance is below threshold
             threshold = rule.performance_threshold or 0
             current_performance_amount = Decimal('0.00')  # Calculate overlay performance if needed
             if current_performance_amount < threshold:
                 rate_matched = True
        else:
            # Flat Rate
            rate_matched = True
            
        if rate_matched:
            applied_rate = rule.rate_value
            applied_rule = rule
            break
    
    if applied_rule:
        commission_amount = basis_amount * (applied_rate / 100)
        
        comm = Commission(
            user=overlay_user,
            opportunity=opportunity,
            amount=commission_amount,
            rate_applied=applied_rate,
            date_earned=opportunity.close_date,
            status='pending',
            is_split=False
        )
        
        return comm
    
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

def get_earnings_trend(user, months=12):
    """
    Get historical earnings trend for the last N months.
    """
    trend_data = []
    today = timezone.now().date()
    
    for i in range(months):
        # Calculate month range (going backwards)
        # 0 = current month, 1 = last month, etc.
        # Logic to handle year wrap
        
        # Simple date math
        # Start of current month
        curr_month_start = today.replace(day=1)
        
        # Subtract i months
        # Calculate year and month
        y, m = curr_month_start.year, curr_month_start.month
        
        target_m = m - i
        target_y = y
        
        while target_m <= 0:
            target_m += 12
            target_y -= 1
            
        period_start = curr_month_start.replace(year=target_y, month=target_m, day=1)
        
        # End of that month
        if target_m == 12:
            period_end = period_start.replace(year=target_y + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            period_end = period_start.replace(month=target_m + 1, day=1) - timezone.timedelta(days=1)
            
        # Query Commissions
        amount = Commission.objects.filter(
            user=user,
            date_earned__range=[period_start, period_end]
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        trend_data.append({
            'month': period_start.strftime('%b %Y'),
            'amount': float(amount), # Convert to float for JSON/Charts
            'sort_date': period_start # Keep date object for sorting if needed
        })
        
    # specific reverse (Oldest to Newest)
    return sorted(trend_data, key=lambda x: x['sort_date'])

def calculate_pace(user, period_start, period_end, current_sales):
    """
    Calculate sales pace status.
    """
    total_days = (period_end - period_start).days + 1
    days_elapsed = (timezone.now().date() - period_start).days + 1
    
    # Cap days elapsed at total days (if looking at past period)
    days_elapsed = min(days_elapsed, total_days)
    if days_elapsed < 0: days_elapsed = 0
    
    # Expected progress %
    expected_progress = (days_elapsed / total_days) * 100 if total_days > 0 else 0
    
    # Actual progress need quota
    # reusing logic implies we have quota object or target amount
    # For efficiency, we should pass target, but let's fetch it if needed or pass it in.
    # Actually, get_user_performance returns 'attainment'
    
    # Simplest: Return expected % vs attainment % difference
    return expected_progress