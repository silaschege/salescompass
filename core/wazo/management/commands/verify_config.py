"""
Management command to verify Wazo and Twilio configuration.
Usage: python manage.py verify_config
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Verify Wazo and Twilio configuration'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SalesCompass Configuration Verification")
        self.stdout.write("=" * 60 + "\n")
        
        errors = []
        warnings = []
        
        # Check Wazo configuration
        self.stdout.write(self.style.HTTP_INFO("Checking Wazo configuration..."))
        
        wazo_required = ['WAZO_API_URL', 'WAZO_API_KEY']
        for var in wazo_required:
            value = getattr(settings, var, None)
            if value:
                self.stdout.write(f"  ✓ {var}: configured")
            else:
                errors.append(f"{var} is not set")
                self.stdout.write(self.style.ERROR(f"  ✗ {var}: missing"))
        
        # Optional Wazo settings
        wazo_optional = [
            'WAZO_TENANT_UUID', 'WAZO_CALLD_URL', 'WAZO_CHATD_URL',
            'WAZO_WEBHOOK_SECRET', 'WAZO_DEFAULT_SMS_NUMBER'
        ]
        for var in wazo_optional:
            value = getattr(settings, var, None)
            if value:
                self.stdout.write(f"  ✓ {var}: configured")
            else:
                warnings.append(f"{var} is not set (optional)")
        
        # Check Twilio configuration
        self.stdout.write(self.style.HTTP_INFO("\nChecking Twilio configuration..."))
        
        twilio_vars = [
            'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_SIP_DOMAIN',
            'TWILIO_CALLER_ID'
        ]
        for var in twilio_vars:
            value = getattr(settings, var, None)
            if value:
                # Mask sensitive values
                display = value[:8] + "..." if len(value) > 10 else "configured"
                self.stdout.write(f"  ✓ {var}: {display}")
            else:
                errors.append(f"{var} is not set")
                self.stdout.write(self.style.ERROR(f"  ✗ {var}: missing"))
        
        # Check Twilio WhatsApp
        self.stdout.write(self.style.HTTP_INFO("\nChecking Twilio WhatsApp..."))
        
        wa_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
        wa_sandbox = getattr(settings, 'TWILIO_WHATSAPP_SANDBOX', True)
        
        if wa_number:
            self.stdout.write(f"  ✓ TWILIO_WHATSAPP_NUMBER: {wa_number}")
            if wa_sandbox:
                self.stdout.write(self.style.WARNING("  ⚠ Running in SANDBOX mode"))
            else:
                self.stdout.write(f"  ✓ Running in PRODUCTION mode")
        else:
            warnings.append("TWILIO_WHATSAPP_NUMBER is not set")
            self.stdout.write(self.style.WARNING("  ⚠ TWILIO_WHATSAPP_NUMBER: not configured"))
        
        # Check WebRTC
        self.stdout.write(self.style.HTTP_INFO("\nChecking WebRTC configuration..."))
        
        webrtc_enabled = getattr(settings, 'WEBRTC_ENABLED', False)
        if webrtc_enabled:
            self.stdout.write(f"  ✓ WEBRTC_ENABLED: True")
            stun = getattr(settings, 'STUN_SERVER', None)
            turn = getattr(settings, 'TURN_SERVER', None)
            if stun:
                self.stdout.write(f"  ✓ STUN_SERVER: {stun}")
            if turn:
                self.stdout.write(f"  ✓ TURN_SERVER: configured")
            else:
                warnings.append("TURN_SERVER not set (may cause issues behind NAT)")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ WEBRTC_ENABLED: False (softphone disabled)"))
        
        # Test Wazo connectivity
        self.stdout.write(self.style.HTTP_INFO("\nTesting Wazo connectivity..."))
        try:
            from wazo.client import wazo_client
            if wazo_client.is_configured():
                health = wazo_client.health_check()
                for service, status in health.items():
                    if status:
                        self.stdout.write(f"  ✓ wazo-{service}: connected")
                    else:
                        warnings.append(f"wazo-{service} is not responding")
                        self.stdout.write(self.style.WARNING(f"  ⚠ wazo-{service}: not responding"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ Wazo client not configured"))
        except Exception as e:
            errors.append(f"Wazo connectivity test failed: {e}")
            self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
        
        # Test Twilio connectivity
        self.stdout.write(self.style.HTTP_INFO("\nTesting Twilio connectivity..."))
        try:
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            
            if account_sid and auth_token:
                from twilio.rest import Client
                client = Client(account_sid, auth_token)
                account = client.api.accounts(account_sid).fetch()
                self.stdout.write(f"  ✓ Connected to Twilio: {account.friendly_name}")
            else:
                self.stdout.write(self.style.WARNING("  ⚠ Twilio credentials not configured"))
        except ImportError:
            warnings.append("Twilio package not installed")
            self.stdout.write(self.style.WARNING("  ⚠ Twilio package not installed (pip install twilio)"))
        except Exception as e:
            errors.append(f"Twilio connectivity failed: {e}")
            self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        if errors:
            self.stdout.write(self.style.ERROR(f"Found {len(errors)} error(s):"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  • {error}"))
        
        if warnings:
            self.stdout.write(self.style.WARNING(f"\nFound {len(warnings)} warning(s):"))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  • {warning}"))
        
        if not errors:
            self.stdout.write(self.style.SUCCESS("\n✓ Configuration verification passed!"))
        else:
            self.stdout.write(self.style.ERROR("\n✗ Configuration verification failed!"))
        
        self.stdout.write("=" * 60 + "\n")
