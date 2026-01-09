# payment_providers.py
"""Abstract payment provider interface and concrete implementations.

This module defines a base class `PaymentProvider` that outlines the required
methods for any payment service (e.g., Stripe, M-Pesa, PayPal, etc.). Concrete
providers implement these methods using the service's SDK or API.

The design allows the rest of the codebase to interact with a generic
`PaymentProvider` instance without hard‑coding Stripe. The active provider
is selected from the database (PaymentProviderConfig model).
"""

import abc
import logging
from typing import Any, Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaymentProvider(abc.ABC):
    """Abstract base class for payment providers.

    Sub‑classes must implement the following methods:
    * ``create_payment_intent`` – create a pending payment for an invoice.
    * ``capture_payment`` – capture/confirm a pending payment.
    * ``refund_payment`` – issue a refund for a captured payment.
    * ``get_checkout_url`` – get a checkout URL for customer payment.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._configure()

    @abc.abstractmethod
    def _configure(self) -> None:
        """Configure the SDK/client using ``self.config``."""

    @abc.abstractmethod
    def create_payment_intent(
        self, 
        amount: Decimal, 
        currency: str = "usd", 
        metadata: Dict[str, Any] = None
    ) -> Any:
        """Create a payment intent (or equivalent) and return the provider object."""

    @abc.abstractmethod
    def capture_payment(self, intent_id: str) -> Any:
        """Capture/confirm a previously created payment intent."""

    @abc.abstractmethod
    def refund_payment(self, payment_id: str, amount: Decimal = None) -> Any:
        """Refund a captured payment. ``amount`` can be ``None`` to refund full amount."""

    @abc.abstractmethod
    def get_checkout_url(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Get a checkout URL for customer-facing payment."""

    @abc.abstractmethod
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify a payment transaction status."""


# ---------------------------------------------------------------------------
# Stripe implementation
# ---------------------------------------------------------------------------

class StripeProvider(PaymentProvider):
    """Concrete provider for Stripe.

    The implementation below is deliberately lightweight – it does **not** import
    the real ``stripe`` package to keep the project runnable without external
    dependencies. In a production environment you would replace the stubbed
    logic with calls to ``stripe.PaymentIntent.create`` etc.
    """

    def _configure(self) -> None:
        # In a real implementation you would set ``stripe.api_key`` here.
        self.api_key = self.config.get("api_key", "sk_test_placeholder")
        self.publishable_key = self.config.get("publishable_key", "pk_test_placeholder")
        logger.debug("StripeProvider configured with api_key=%s", self.api_key[:10] + "...")

    def create_payment_intent(
        self, 
        amount: Decimal, 
        currency: str = "usd", 
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # Stubbed response mimicking Stripe's PaymentIntent object.
        intent = {
            "id": f"pi_{int(amount * 100)}",
            "amount": int(amount * 100),  # amount in cents
            "currency": currency,
            "status": "requires_payment_method",
            "metadata": metadata or {},
        }
        logger.info("Created Stripe payment intent: %s", intent["id"])
        return intent

    def capture_payment(self, intent_id: str) -> Dict[str, Any]:
        # Stubbed capture – in reality you would call ``stripe.PaymentIntent.capture``.
        result = {"id": intent_id, "status": "succeeded"}
        logger.info("Captured Stripe payment intent: %s", intent_id)
        return result

    def refund_payment(self, payment_id: str, amount: Decimal = None) -> Dict[str, Any]:
        # Stubbed refund – replace with ``stripe.Refund.create``.
        refund = {"id": f"re_{payment_id}", "payment_id": payment_id, "amount": float(amount) if amount else None}
        logger.info("Refunded Stripe payment %s (amount=%s)", payment_id, amount)
        return refund

    def get_checkout_url(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        # Stubbed checkout URL
        session_id = f"cs_{int(amount * 100)}"
        logger.info("Created Stripe checkout session: %s", session_id)
        return f"https://checkout.stripe.com/pay/{session_id}"

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        # Stubbed verification
        return {"id": transaction_id, "status": "succeeded", "verified": True}


# ---------------------------------------------------------------------------
# M-Pesa implementation
# ---------------------------------------------------------------------------

class MPesaProvider(PaymentProvider):
    """Concrete provider for M-Pesa (Safaricom Kenya).
    
    This is a simplified implementation. In production, you would integrate
    with Safaricom's Daraja API for STK Push and payment verification.
    """

    def _configure(self) -> None:
        self.consumer_key = self.config.get("consumer_key", "")
        self.consumer_secret = self.config.get("consumer_secret", "")
        self.business_short_code = self.config.get("business_short_code", "")
        self.passkey = self.config.get("passkey", "")
        logger.debug("MPesaProvider configured for shortcode: %s", self.business_short_code)

    def create_payment_intent(
        self, 
        amount: Decimal, 
        currency: str = "KES", 
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # Stubbed M-Pesa STK Push initiation
        phone_number = metadata.get("phone_number", "+254700000000") if metadata else "+254700000000"
        
        intent = {
            "id": f"mpesa_{int(amount)}_{phone_number[-4:]}",
            "amount": int(amount),
            "currency": currency,
            "status": "pending",
            "phone_number": phone_number,
            "metadata": metadata or {},
        }
        logger.info("Initiated M-Pesa STK Push: %s to %s", intent["id"], phone_number)
        return intent

    def capture_payment(self, intent_id: str) -> Dict[str, Any]:
        # M-Pesa doesn't have a separate capture step - payment is immediate
        result = {"id": intent_id, "status": "succeeded"}
        logger.info("M-Pesa payment completed: %s", intent_id)
        return result

    def refund_payment(self, payment_id: str, amount: Decimal = None) -> Dict[str, Any]:
        # M-Pesa refund (reversal)
        refund = {
            "id": f"mpesa_refund_{payment_id}",
            "payment_id": payment_id,
            "amount": float(amount) if amount else None,
            "status": "completed"
        }
        logger.info("Initiated M-Pesa refund for %s (amount=%s)", payment_id, amount)
        return refund

    def get_checkout_url(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        # M-Pesa typically uses STK Push, not a URL
        # Return a placeholder or instructions page
        return f"/billing/mpesa-payment/?amount={amount}&currency={currency}"

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        # Stubbed verification - would call M-Pesa query API
        return {
            "id": transaction_id,
            "status": "succeeded",
            "verified": True,
            "mpesa_receipt": f"MPR{transaction_id}"
        }


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
 
# ... existing code ...
def get_provider(provider_name: str = None, tenant_id: str = None) -> PaymentProvider:
    """Factory that returns a configured ``PaymentProvider`` instance.

    Loads configuration from the database (PaymentProviderConfig model).
    
    Args:
        provider_name: Name of the provider (stripe, mpesa, etc.)
        tenant_id: Optional tenant ID to load tenant-specific credentials
     
    Returns:
        Configured PaymentProvider instance
    """
    from .models import PaymentProviderConfig
    
    # Load provider config from database
    if provider_name:
        try:
            if tenant_id:
                # Filter by tenant if provided
                provider_config = PaymentProviderConfig.objects.get(
                    provider_config_name=provider_name,
                    config_is_active=True,
                    tenant_id=tenant_id
                )
            else:
                provider_config = PaymentProviderConfig.objects.get(
                    provider_config_name=provider_name,
                    config_is_active=True
                )
        except PaymentProviderConfig.DoesNotExist:
            raise ValueError(f"Payment provider '{provider_name}' not found or not active")
    else:
        # Get default active provider
        if tenant_id:
            provider_config = PaymentProviderConfig.objects.filter(
                config_is_active=True, 
                tenant_id=tenant_id
            ).first()
        else:
            provider_config = PaymentProviderConfig.objects.filter(config_is_active=True).first()
        
        if not provider_config:
            raise ValueError("No active payment providers configured")
    
    # Get effective configuration
    config = {
        'api_key': provider_config.api_key,
        'secret_key': provider_config.secret_key,
        'webhook_secret': provider_config.webhook_secret,
        'display_name': provider_config.display_name
    }
    
    # Instantiate appropriate provider class
    provider_classes = {
        "stripe": StripeProvider,
        "mpesa": MPesaProvider,
        # Add more providers here as needed
    }
    
    provider_class = provider_classes.get(provider_config.provider_config_name)
    if not provider_class:
        raise ValueError(f"No implementation found for provider: {provider_config.provider_config_name}")
    
    return provider_class(config)
# ... existing code ...

def get_available_providers(tenant_id: str = None, for_customers: bool = False) -> list:
    """Get list of available payment providers.
    
    Args:
        tenant_id: Optional tenant ID to filter by tenant configuration
        for_customers: If True, only return providers enabled for customer checkout
    
    Returns:
        List of provider dictionaries with name, display_name, etc.
    """
    from .models import PaymentProviderConfig, TenantPaymentConfig
    
    if tenant_id:
        # Get tenant-enabled providers
        tenant_configs = TenantPaymentConfig.objects.filter(
            tenant_id=tenant_id,
            provider__is_active=True
        ).select_related('provider')
        
        if for_customers:
            tenant_configs = tenant_configs.filter(is_enabled_for_customers=True)
        
        return [
            {
                "name": tc.provider.name,
                "display_name": tc.custom_label or tc.provider.display_name,
                "logo_url": tc.provider.logo_url,
                "supported_currencies": tc.provider.supported_currencies,
            }
            for tc in tenant_configs
        ]
    else:
        # Get all active platform providers
        providers = PaymentProviderConfig.objects.filter(is_active=True)
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "logo_url": p.logo_url,
                "supported_currencies": p.supported_currencies,
            }
            for p in providers
        ]
