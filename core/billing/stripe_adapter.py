"""
Stripe Payment Adapter for SalesCompass CRM

Provides integration with Stripe for:
- Subscription management
- Payment processing
- Invoice handling
- Customer management
- Webhook processing
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class StripeCustomer:
    """Stripe customer representation."""
    id: str
    email: str
    name: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class StripeSubscription:
    """Stripe subscription representation."""
    id: str
    customer_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    plan_id: str
    price_id: str
    quantity: int = 1
    metadata: Optional[Dict] = None


@dataclass
class StripeInvoice:
    """Stripe invoice representation."""
    id: str
    customer_id: str
    subscription_id: Optional[str]
    status: str
    amount_due: int
    amount_paid: int
    currency: str
    invoice_pdf: Optional[str] = None


class StripeNotConfiguredError(Exception):
    """Raised when Stripe is not configured."""
    pass


class StripeAPIError(Exception):
    """Raised when Stripe API request fails."""
    pass


class StripeAdapter:
    """
    Stripe API adapter for SalesCompass.
    
    Usage:
        from billing.stripe_adapter import stripe_adapter
        
        # Create a customer
        customer = stripe_adapter.create_customer(
            email='user@example.com',
            name='John Doe',
            tenant_id='tenant_abc'
        )
        
        # Create a subscription
        subscription = stripe_adapter.create_subscription(
            customer_id=customer.id,
            price_id='price_xxx'
        )
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        self._stripe = None
    
    @property
    def stripe(self):
        """Lazy load Stripe library."""
        if self._stripe is None:
            try:
                import stripe
                stripe.api_key = self.api_key
                self._stripe = stripe
            except ImportError:
                raise StripeNotConfiguredError("Stripe library not installed")
        return self._stripe
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(self.api_key)
    
    def create_customer(
        self,
        email: str,
        name: str = None,
        tenant_id: str = None,
        metadata: Dict = None
    ) -> Optional[StripeCustomer]:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            tenant_id: SalesCompass tenant ID
            metadata: Additional metadata
        
        Returns:
            StripeCustomer object or None if failed
        """
        if not self.is_configured():
            logger.warning("Stripe not configured")
            return None
        
        try:
            customer_metadata = metadata or {}
            if tenant_id:
                customer_metadata['tenant_id'] = tenant_id
            
            customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata=customer_metadata,
            )
            
            result = StripeCustomer(
                id=customer.id,
                email=customer.email,
                name=customer.name,
                metadata=customer.metadata,
            )
            
            self._emit_event('customer.created', {
                'stripe_customer_id': customer.id,
                'email': email,
                'tenant_id': tenant_id,
            })
            
            return result
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise StripeAPIError(str(e))
    
    def get_customer(self, customer_id: str) -> Optional[StripeCustomer]:
        """Get a Stripe customer by ID."""
        if not self.is_configured():
            return None
        
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return StripeCustomer(
                id=customer.id,
                email=customer.email,
                name=customer.name,
                metadata=customer.metadata,
            )
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting customer: {e}")
            return None
    
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        trial_days: int = None,
        metadata: Dict = None
    ) -> Optional[StripeSubscription]:
        """
        Create a new subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            quantity: Number of units
            trial_days: Trial period in days
            metadata: Additional metadata
        
        Returns:
            StripeSubscription object or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            params = {
                'customer': customer_id,
                'items': [{'price': price_id, 'quantity': quantity}],
                'metadata': metadata or {},
            }
            
            if trial_days:
                params['trial_period_days'] = trial_days
            
            subscription = self.stripe.Subscription.create(**params)
            
            result = StripeSubscription(
                id=subscription.id,
                customer_id=subscription.customer,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                plan_id=subscription['items'].data[0].plan.id,
                price_id=subscription['items'].data[0].price.id,
                quantity=quantity,
                metadata=subscription.metadata,
            )
            
            self._emit_event('subscription.created', {
                'stripe_subscription_id': subscription.id,
                'stripe_customer_id': customer_id,
                'price_id': price_id,
                'status': subscription.status,
            })
            
            return result
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise StripeAPIError(str(e))
    
    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> bool:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period
        
        Returns:
            True if successful
        """
        if not self.is_configured():
            return False
        
        try:
            if at_period_end:
                self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                self.stripe.Subscription.delete(subscription_id)
            
            self._emit_event('subscription.cancelled', {
                'stripe_subscription_id': subscription_id,
                'at_period_end': at_period_end,
            })
            
            return True
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            return False
    
    def update_subscription(
        self,
        subscription_id: str,
        price_id: str = None,
        quantity: int = None
    ) -> Optional[StripeSubscription]:
        """
        Update a subscription (change plan or quantity).
        
        Args:
            subscription_id: Stripe subscription ID
            price_id: New price ID (optional)
            quantity: New quantity (optional)
        
        Returns:
            Updated StripeSubscription or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            
            update_params = {}
            
            if price_id or quantity:
                item = subscription['items'].data[0]
                items_update = {'id': item.id}
                
                if price_id:
                    items_update['price'] = price_id
                if quantity:
                    items_update['quantity'] = quantity
                
                update_params['items'] = [items_update]
                update_params['proration_behavior'] = 'create_prorations'
            
            if update_params:
                subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    **update_params
                )
            
            return StripeSubscription(
                id=subscription.id,
                customer_id=subscription.customer,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                plan_id=subscription['items'].data[0].plan.id,
                price_id=subscription['items'].data[0].price.id,
                quantity=subscription['items'].data[0].quantity,
                metadata=subscription.metadata,
            )
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[StripeSubscription]:
        """Get subscription details."""
        if not self.is_configured():
            return None
        
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            
            return StripeSubscription(
                id=subscription.id,
                customer_id=subscription.customer,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                plan_id=subscription['items'].data[0].plan.id,
                price_id=subscription['items'].data[0].price.id,
                quantity=subscription['items'].data[0].quantity,
                metadata=subscription.metadata,
            )
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription: {e}")
            return None
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = 'subscription',
        metadata: Dict = None
    ) -> Optional[str]:
        """
        Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            mode: 'subscription' or 'payment'
            metadata: Additional metadata
        
        Returns:
            Checkout session URL or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            
            return session.url
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {e}")
            return None
    
    def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a Stripe Billing Portal session.
        
        Allows customers to manage their subscription.
        
        Returns:
            Portal session URL or None if failed
        """
        if not self.is_configured():
            return None
        
        try:
            session = self.stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return session.url
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal: {e}")
            return None
    
    def get_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[StripeInvoice]:
        """Get customer invoices."""
        if not self.is_configured():
            return []
        
        try:
            invoices = self.stripe.Invoice.list(
                customer=customer_id,
                limit=limit,
            )
            
            return [
                StripeInvoice(
                    id=inv.id,
                    customer_id=inv.customer,
                    subscription_id=inv.subscription,
                    status=inv.status,
                    amount_due=inv.amount_due,
                    amount_paid=inv.amount_paid,
                    currency=inv.currency,
                    invoice_pdf=inv.invoice_pdf,
                )
                for inv in invoices.data
            ]
            
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error getting invoices: {e}")
            return []
    
    def verify_webhook(self, payload: bytes, signature: str) -> Optional[Dict]:
        """
        Verify and parse a webhook payload.
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header
        
        Returns:
            Event data dict or None if invalid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return None
        
        try:
            event = self.stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return event
            
        except (ValueError, self.stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook verification failed: {e}")
            return None
    
    def handle_webhook_event(self, event: Dict) -> bool:
        """
        Handle a webhook event.
        
        Args:
            event: Verified Stripe event
        
        Returns:
            True if handled successfully
        """
        event_type = event.get('type')
        data = event.get('data', {}).get('object', {})
        
        handlers = {
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.paid': self._handle_invoice_paid,
            'invoice.payment_failed': self._handle_payment_failed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                handler(data)
                return True
            except Exception as e:
                logger.error(f"Error handling webhook {event_type}: {e}")
                return False
        
        logger.debug(f"Unhandled webhook event: {event_type}")
        return True
    
    def _handle_subscription_created(self, data: Dict) -> None:
        """Handle subscription created webhook."""
        self._sync_subscription_to_crm(data)
    
    def _handle_subscription_updated(self, data: Dict) -> None:
        """Handle subscription updated webhook."""
        self._sync_subscription_to_crm(data)
    
    def _handle_subscription_deleted(self, data: Dict) -> None:
        """Handle subscription deleted webhook."""
        try:
            from billing.models import Subscription
            
            Subscription.objects.filter(
                stripe_subscription_id=data.get('id')
            ).update(status='cancelled')
            
        except ImportError:
            pass
    
    def _handle_invoice_paid(self, data: Dict) -> None:
        """Handle invoice paid webhook."""
        try:
            from billing.models import Invoice
            
            Invoice.objects.filter(
                stripe_invoice_id=data.get('id')
            ).update(status='paid', paid_at=timezone.now())
            
        except ImportError:
            pass
    
    def _handle_payment_failed(self, data: Dict) -> None:
        """Handle payment failed webhook."""
        self._emit_event('payment.failed', {
            'stripe_invoice_id': data.get('id'),
            'stripe_customer_id': data.get('customer'),
            'amount_due': data.get('amount_due'),
        })
    
    def _sync_subscription_to_crm(self, data: Dict) -> None:
        """Sync Stripe subscription to CRM billing model."""
        try:
            from billing.models import Subscription
            
            Subscription.objects.update_or_create(
                stripe_subscription_id=data.get('id'),
                defaults={
                    'status': data.get('status'),
                    'current_period_start': datetime.fromtimestamp(data.get('current_period_start')),
                    'current_period_end': datetime.fromtimestamp(data.get('current_period_end')),
                }
            )
        except ImportError:
            pass
    
    def _emit_event(self, event_type: str, payload: Dict) -> None:
        """Emit billing event to event bus."""
        try:
            from core.event_bus import emit
            emit(event_type, payload)
        except Exception as e:
            logger.debug(f"Failed to emit billing event: {e}")


stripe_adapter = StripeAdapter()
