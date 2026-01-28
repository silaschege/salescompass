from decimal import Decimal
from django.utils import timezone
from .models import PriceList, PriceListItem, PricingTier, Coupon, Promotion
import barcode
from barcode.writer import ImageWriter
import qrcode
import io

class PricingService:
    @staticmethod
    def get_price(product, account=None, quantity=1, currency='USD'):
        """
        Get the unit price for a product given the context.
        Hierarchy:
        1. Account-specific Price List (if exists) -> PriceListItem
        2. Pricing Tiers (Volume Discounts)
        3. Product Base Price
        """
        qty = int(quantity)
        
        # 1. Price List
        if account and account.price_list and account.price_list.is_active:
             price_item = PriceListItem.objects.filter(
                 price_list=account.price_list,
                 product=product,
                 min_quantity__lte=qty
             ).order_by('-min_quantity').first()
             
             if price_item:
                 return price_item.price

        # 2. Volume Pricing Tiers (Global)
        # Find applicable tier with highest min_quantity that is <= current qty
        tier = PricingTier.objects.filter(
            product=product,
            min_quantity__lte=qty
        ).order_by('-min_quantity').first()
        
        if tier:
            # Check max_quantity
            if tier.max_quantity is None or qty <= tier.max_quantity:
                if tier.unit_price > 0:
                    return tier.unit_price
                elif tier.discount_percent > 0:
                    discount = product.base_price * (Decimal(str(tier.discount_percent)) / Decimal('100'))
                    return product.base_price - discount

        # 3. Base Price
        return product.base_price

    @staticmethod
    def calculate_line_total(product, quantity, account=None):
        """
        Calculate total for a line item.
        """
        unit_price = PricingService.get_price(product, account, quantity)
        return unit_price * Decimal(str(quantity))


class PromotionService:
    @staticmethod
    def validate_coupon(code, tenant, user=None, cart_total=Decimal('0')):
        """
        Validate a coupon code. Returns (is_valid, message, coupon_obj).
        """
        now = timezone.now()
        try:
            coupon = Coupon.objects.get(code=code, tenant=tenant)
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code.", None
            
        if not coupon.is_active:
            return False, "Coupon is inactive.", None
            
        if coupon.start_date > now:
            return False, "Coupon is not yet valid.", None
            
        if coupon.end_date < now:
            return False, "Coupon has expired.", None
            
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return False, "Coupon usage limit reached.", None
            
        if cart_total < coupon.min_purchase_amount:
            return False, f"Minimum purchase of {coupon.min_purchase_amount} required.", None
            
        return True, "Coupon applied successfully.", coupon

    @staticmethod
    def calculate_discount(coupon, cart_total):
        """
        Calculate discount amount for a validated coupon.
        """
        if coupon.discount_type == 'fixed':
            return min(coupon.discount_value, cart_total) # Cannot discount more than total
        elif coupon.discount_type == 'percentage':
            return cart_total * (coupon.discount_value / Decimal('100'))
        return Decimal('0')

    @staticmethod
    def use_coupon(coupon):
        """
        Increment usage count.
        """
        coupon.used_count += 1
        coupon.save()


class BarcodeService:
    @staticmethod
    def generate_barcode(code, barcode_type='code128'):
        """
        Generate a barcode image. Returns bytes.
        """
        try:
            # Use python-barcode
            BARCODE = barcode.get_barcode_class(barcode_type)
            # Create barcode object. We write to a BytesIO buffer.
            # writer=ImageWriter() creates a PNG (requires Pillow)
            rv = io.BytesIO()
            code_obj = BARCODE(code, writer=ImageWriter())
            code_obj.write(rv)
            return rv.getvalue()
        except Exception as e:
            print(f"Barcode generation error: {e}")
            return None

    @staticmethod
    def generate_qrcode(data):
        """
        Generate a QR code image. Returns bytes.
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            rv = io.BytesIO()
            img.save(rv, format="PNG")
            return rv.getvalue()
        except Exception as e:
            print(f"QR generation error: {e}")
            return None
