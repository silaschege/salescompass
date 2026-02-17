from .models import CustomerLoyalty, LoyaltyTransaction, LoyaltyProgram
from accounts.models import Account
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from accounting.models import AccountingIntegration
from accounting.services import JournalService

class LoyaltyService:
    """
    Service to manage customer loyalty points and transactions.
    """
    
    @staticmethod
    def award_points(customer, points, description, sale_amount=0, reference=None, member=None):
        """
        Awards points to a customer loyalty account.
        Implements IFRS 15 Revenue Allocation if sale_amount is provided.
        """
        if points <= 0:
            return None
            
        loyalty_account, created = CustomerLoyalty.objects.get_or_create(
            customer=customer,
            defaults={
                'tenant': customer.tenant,
                'program': LoyaltyProgram.objects.filter(tenant=customer.tenant).first()
            }
        )
        
        program = loyalty_account.program
        if not program:
            return None
            
        allocated_revenue = Decimal('0.00')
        
        # IFRS 15: Relative Stand-alone Selling Price Allocation
        if sale_amount > 0:
            point_market_value = Decimal(points) * program.redemption_conversion_rate
            # Formula: (Point Value / (Sale Price + Point Value)) * Sale Price
            total_fair_value = Decimal(sale_amount) + point_market_value
            if total_fair_value > 0:
                allocated_revenue = (point_market_value / total_fair_value) * Decimal(sale_amount)
                allocated_revenue = allocated_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        transaction = LoyaltyTransaction.objects.create(
            tenant=customer.tenant,
            loyalty_account=loyalty_account,
            transaction_type='earn',
            points=points,
            allocated_revenue=allocated_revenue,
            description=description,
            reference_number=reference or '',
            processed_by=member
        )
        
        # Accounting: Record Contract Liability (IFRS 15)
        if allocated_revenue > 0:
            LoyaltyService._record_accounting_event(
                transaction, 
                'loyalty_earned', 
                allocated_revenue,
                member
            )
            
        return transaction

    @staticmethod
    def redeem_points(customer_loyalty, points, description, member=None):
        """
        Redeems points and recognized deferred revenue.
        """
        if customer_loyalty.points_balance < points:
            raise ValueError("Insufficient points balance.")
            
        # Calculate revenue to recognize based on FIFO/Average cost of deferred points
        # For simplicity, we use the average allocation or current market value
        program = customer_loyalty.program
        redemption_value = (Decimal(points) * program.redemption_conversion_rate).quantize(Decimal('0.01'))
        
        transaction = LoyaltyTransaction.objects.create(
            tenant=customer_loyalty.tenant,
            loyalty_account=customer_loyalty,
            transaction_type='redeem',
            points=-points,
            description=description,
            processed_by=member
        )
        
        # Accounting: Dr Deferred Revenue / Cr Sale Revenue
        LoyaltyService._record_accounting_event(
            transaction,
            'loyalty_redeemed',
            redemption_value,
            member
        )
        
        return transaction

    @staticmethod
    def recognize_breakage(tenant):
        """
        Recognizes revenue for expired points (Breakage).
        """
        today = timezone.now().date()
        expired_transactions = LoyaltyTransaction.objects.filter(
            tenant=tenant,
            transaction_type='earn',
            is_expired=False,
            expiry_date__lt=today,
            loyalty_account__points_balance__gt=0
        )
        
        for tx in expired_transactions:
            # Recognize the remaining deferred revenue as breakage income
            # This is a simplified per-transaction breakage model
            if tx.allocated_revenue > 0:
                LoyaltyService._record_accounting_event(
                    tx,
                    'loyalty_breakage',
                    tx.allocated_revenue, # Assuming full breakage of the deferral
                    None
                )
            tx.is_expired = True
            tx.save()
            
            # Record negative adjustment for the points
            LoyaltyTransaction.objects.create(
                tenant=tenant,
                loyalty_account=tx.loyalty_account,
                transaction_type='expire',
                points=-tx.points,
                description=f"Points expired from Transaction {tx.id}"
            )

    @staticmethod
    def _record_accounting_event(transaction, event_type, amount, user):
        """
        Helper to create journal entries based on integration rules.
        """
        try:
            rule = AccountingIntegration.objects.get(
                tenant=transaction.tenant,
                event_type=event_type,
                is_active=True
            )
            
            if not rule.debit_account or not rule.credit_account:
                return
                
            lines = [
                {
                    'account': rule.debit_account,
                    'debit': amount,
                    'credit': Decimal('0.00'),
                    'description': f"Loyalty {event_type} - Ref {transaction.id}"
                },
                {
                    'account': rule.credit_account,
                    'debit': Decimal('0.00'),
                    'credit': amount,
                    'description': f"Loyalty {event_type} - Ref {transaction.id}"
                }
            ]
            
            JournalService.create_journal_entry(
                tenant=transaction.tenant,
                date=timezone.now().date(),
                description=f"Loyalty Financial Adjustment: {event_type}",
                user=user or transaction.loyalty_account.tenant.tenant_admin, # Fallback to admin
                lines=lines,
                reference=f"LOY-{transaction.id}",
                status='posted',
                related_object=transaction
            )
        except AccountingIntegration.DoesNotExist:
            pass # No rule configured, skip accounting injection


    @staticmethod
    def process_campaign_engagement(account, campaign):
        """
        Awards bonus points if the campaign has them configured.
        """
        if campaign.bonus_points > 0:
            return LoyaltyService.award_points(
                customer=account,
                points=campaign.bonus_points,
                description=f"Bonus points for campaign: {campaign.campaign_name}",
                reference=f"CAMPAIGN-{campaign.id}"
            )
        return None
