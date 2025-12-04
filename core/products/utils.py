from .models import PricingTier, ProductBundle

def get_product_price(product_id: int, quantity: int = 1) -> dict:
    """Get price for a product based on quantity."""
    product = Product.objects.get(id=product_id)
    
    if product.pricing_model == 'flat':
        return {
            'unit_price': product.base_price,
            'total_price': product.base_price * quantity,
            'discount': 0.0
        }
    elif product.pricing_model == 'per_unit':
        return {
            'unit_price': product.base_price,
            'total_price': product.base_price * quantity,
            'discount': 0.0
        }
    elif product.pricing_model == 'tiered':
        tier = PricingTier.objects.filter(
            product_id=product_id,
            min_quantity__lte=quantity
        ).order_by('-min_quantity').first()
        
        if tier:
            unit_price = tier.unit_price
            discount = tier.discount_percent
        else:
            unit_price = product.base_price
            discount = 0.0
        
        total = unit_price * quantity
        if discount > 0:
            total = total * (1 - discount / 100)
        
        return {
            'unit_price': unit_price,
            'total_price': total,
            'discount': discount
        }
    else:  # subscription
        return {
            'unit_price': product.base_price,
            'total_price': product.base_price * quantity,
            'discount': 0.0
        }


def get_bundle_price(bundle_id: int) -> dict:
    """Get total price for a bundle."""
    bundle = ProductBundle.objects.get(id=bundle_id)
    
    if bundle.bundle_price:
        return {
            'total_price': bundle.bundle_price,
            'savings': None
        }
    
    # Calculate from individual products
    total = 0
    for item in bundle.bundleitem_set.all():
        price_info = get_product_price(item.product_id, item.quantity)
        total += price_info['total_price']
    
    return {
        'total_price': total,
        'savings': None  # Could compare to non-bundle price
    }


def validate_product_dependencies(product_ids: list) -> dict:
    """Validate that all dependencies are satisfied."""
    errors = []
    product_set = set(product_ids)
    
    for product_id in product_ids:
        dependencies = ProductDependency.objects.filter(product_id=product_id)
        for dep in dependencies:
            if dep.required_product_id not in product_set:
                errors.append(
                    f"{dep.product.name} requires {dep.required_product.name}"
                )
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def generate_sku(product_name: str, category: str = None) -> str:
    """
    Generate a unique SKU based on product name and category.
    Format: CAT-PROD-001
    """
    from django.utils.text import slugify
    
    # Get base SKU
    if category:
        cat_prefix = slugify(category)[:3].upper()
    else:
        cat_prefix = "GEN"
    
    prod_slug = slugify(product_name)[:10].upper()
    
    # Find next available number
    existing_skus = Product.objects.filter(
        sku__regex=f"^{cat_prefix}-{prod_slug}-[0-9]+$"
    ).values_list('sku', flat=True)
    
    if existing_skus:
        numbers = [int(sku.split('-')[-1]) for sku in existing_skus]
        next_num = max(numbers) + 1
    else:
        next_num = 1
    
    return f"{cat_prefix}-{prod_slug}-{next_num:03d}"