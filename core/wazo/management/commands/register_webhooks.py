"""
Management command to register webhooks with Wazo Platform.
Usage: python manage.py register_webhooks --base-url=https://your-domain.com
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from wazo.client import WazoAPIClient


WEBHOOK_EVENTS = [
    # Call events
    'call_created',
    'call_answered', 
    'call_ended',
    'call_updated',
    'call_held',
    'call_resumed',
    # SMS events
    'chatd_user_room_message_created',
    # Voicemail events
    'user_voicemail_message_created',
    # WhatsApp events (if using Wazo for WhatsApp)
    'whatsapp_message_received',
    'whatsapp_message_status_updated',
]


class Command(BaseCommand):
    help = 'Register webhook subscriptions with Wazo Platform'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', type=str, required=True,
                          help='Base URL for webhook callbacks (e.g., https://crm.salescompass.io)')
        parser.add_argument('--delete-existing', action='store_true',
                          help='Delete existing SalesCompass webhooks before creating new ones')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be done without making changes')

    def handle(self, *args, **options):
        base_url = options['base_url'].rstrip('/')
        delete_existing = options['delete_existing']
        dry_run = options['dry_run']
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Wazo Webhook Registration")
        self.stdout.write("=" * 50 + "\n")
        
        client = WazoAPIClient()
        
        if not client.is_configured():
            self.stdout.write(self.style.ERROR(
                "Wazo is not configured. Set WAZO_API_URL and WAZO_API_KEY."
            ))
            return
        
        webhook_url = f"{base_url}/wazo/webhooks/"
        secret = getattr(settings, 'WAZO_WEBHOOK_SECRET', '')
        
        self.stdout.write(f"Webhook URL: {webhook_url}")
        self.stdout.write(f"Events to subscribe: {len(WEBHOOK_EVENTS)}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes will be made\n"))
        
        # Delete existing webhooks if requested
        if delete_existing and not dry_run:
            self.stdout.write(self.style.WARNING("\nDeleting existing webhooks..."))
            try:
                response = client.get('subscriptions', service='webhookd')
                if response:
                    for sub in response.get('items', []):
                        if 'salescompass' in sub.get('name', '').lower():
                            client.delete(f"subscriptions/{sub['uuid']}", service='webhookd')
                            self.stdout.write(f"  Deleted: {sub['name']}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error: {e}"))
        
        # Create new subscription
        self.stdout.write(self.style.HTTP_INFO("\nCreating webhook subscription..."))
        
        subscription = {
            'name': 'salescompass-crm-events',
            'service': 'http',
            'config': {
                'url': webhook_url,
                'method': 'post',
                'content_type': 'application/json',
            },
            'events': WEBHOOK_EVENTS,
            'events_user_uuid': None,
            'events_wazo_uuid': None,
        }
        
        if secret:
            subscription['config']['verify_certificate'] = True
        
        if dry_run:
            self.stdout.write("\nWould create subscription:")
            self.stdout.write(f"  Name: {subscription['name']}")
            self.stdout.write(f"  URL: {subscription['config']['url']}")
            self.stdout.write(f"  Events: {', '.join(WEBHOOK_EVENTS[:5])}...")
        else:
            try:
                response = client.post('subscriptions', service='webhookd', data=subscription)
                
                if response and response.get('uuid'):
                    self.stdout.write(self.style.SUCCESS(f"\n✓ Webhook registered successfully!"))
                    self.stdout.write(f"  UUID: {response.get('uuid')}")
                else:
                    self.stdout.write(self.style.ERROR(f"\n✗ Failed to register webhook"))
                    self.stdout.write(f"  Response: {response}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n✗ Error: {e}"))
        
        self.stdout.write("\n" + "=" * 50 + "\n")
