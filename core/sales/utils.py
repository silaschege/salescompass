from decimal import Decimal
from django.utils import timezone
from django.db import models
from .models import SalesCommissionRule, SalesCommission

def calculate_commission(sale):
    """
    Calculate and record commission for a given sale based on active rules.
    """
    if not sale.sales_rep:
        return None

    # Find applicable rules
    # Priority: Specific Product > Product Type > Default (if any)
    
    rules = SalesCommissionRule.objects.filter(
        is_active=True,
        start_date__lte=sale.sale_date.date()
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=sale.sale_date.date())
    )

    # Filter by minimum sales amount
    rules = rules.filter(min_sales_amount__lte=sale.amount)

    applicable_rule = None

    # 1. Check for specific product rule
    specific_rule = rules.filter(specific_product=sale.product).order_by('-percentage').first()
    if specific_rule:
        applicable_rule = specific_rule
    else:
        # 2. Check for product type rule
        type_rule = rules.filter(product_type=sale.product.product_type).order_by('-percentage').first()
        if type_rule:
            applicable_rule = type_rule
        else:
            # 3. Check for generic rule (no specific product or type)
            generic_rule = rules.filter(specific_product__isnull=True, product_type='').order_by('-percentage').first()
            if generic_rule:
                applicable_rule = generic_rule

    if not applicable_rule:
        return None

    # Calculate amount
    commission_amount = Decimal('0.00')
    if applicable_rule.flat_amount > 0:
        commission_amount += applicable_rule.flat_amount
    
    if applicable_rule.percentage > 0:
        commission_amount += (sale.amount * (applicable_rule.percentage / Decimal('100.0')))

    # Create Commission record
    commission = SalesCommission.objects.create(
        sale=sale,
        sales_rep=sale.sales_rep,
        rule_applied=applicable_rule,
        amount=commission_amount,
        status='pending',
        date_earned=timezone.now()
    )

    return commission
