from .models import PricingTier, ProductBundle,Product, BundleItem, ProductDependency, CompetitorProduct, ProductComparison
from django.db import models

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

def validate_bundle_items(bundle_id):
    """Validate that all items in a bundle are active and available"""
    bundle = ProductBundle.objects.get(id=bundle_id)
    inactive_items = BundleItem.objects.filter(
        bundle=bundle,
        product__product_is_active=False
    ).count()
    return inactive_items == 0

def calculate_bundle_savings(bundle_id):
    """Calculate savings from buying bundle vs individual items"""
    bundle = ProductBundle.objects.get(id=bundle_id)
    if bundle.bundle_price:
        individual_total = sum(
            item.product.base_price * item.quantity 
            for item in bundle.bundleitem_set.all()
        )
        savings = individual_total - bundle.bundle_price
        return {
            'individual_total': individual_total,
            'bundle_price': bundle.bundle_price,
            'savings': savings,
            'savings_percentage': (savings / individual_total) * 100 if individual_total > 0 else 0
        }
    return None

def analyze_competitive_position(product_id):
    """Analyze competitive position of a product"""
    try:
        product = Product.objects.get(id=product_id)
        competitors = CompetitorProduct.objects.filter(our_product=product)
        
        if competitors.exists():
            avg_price_diff = competitors.aggregate(
                avg_diff=models.Avg('price_difference_percent')
            )['avg_diff'] or 0
            
            # Count direct vs indirect competitors
            direct_competitors = competitors.filter(is_direct_competitor=True).count()
            indirect_competitors = competitors.filter(is_direct_competitor=False).count()
            
            return {
                'product': product,
                'competitor_count': competitors.count(),
                'direct_competitors': direct_competitors,
                'indirect_competitors': indirect_competitors,
                'average_price_difference': avg_price_diff,
                'position': (
                    'more_expensive' if avg_price_diff > 0 
                    else 'cheaper' if avg_price_diff < 0 
                    else 'equal'
                ),
                'message': (
                    f'This product is {abs(avg_price_diff):.2f}% more expensive than competitors' 
                    if avg_price_diff > 0
                    else f'This product is {abs(avg_price_diff):.2f}% cheaper than competitors' 
                    if avg_price_diff < 0
                    else 'This product is priced equally to competitors'
                )
            }
        else:
            return {
                'product': product,
                'competitor_count': 0,
                'message': 'No competitors mapped for this product'
            }
    except Product.DoesNotExist:
        return {
            'error': 'Product does not exist'
        }


def generate_barcode(sku: str, barcode_type: str = 'code128') -> str:
    """
    Generate barcode image (SVG) for a SKU.
    Returns the SVG content as a string.
    """
    import barcode
    from barcode.writer import SVGWriter
    from io import BytesIO

    try:
        # Get the barcode class
        barcode_class = barcode.get_barcode_class(barcode_type)
        
        # Create barcode object
        # writer=SVGWriter() ensures we get SVG output which is scalable and easy to embed
        rv = BytesIO()
        code = barcode_class(sku, writer=SVGWriter())
        
        # Write to buffer
        code.write(rv)
        
        # Return SVG string
        return rv.getvalue().decode('utf-8')
    except Exception as e:
        # Fallback or error logging
        print(f"Error generating barcode: {e}")
        return None