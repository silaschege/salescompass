"""
Management command to set up user extensions.
Usage: python manage.py setup_extensions --tenant-id=1 --start-ext=1001
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wazo.models import WazoExtension
from tenants.models import Tenant


User = get_user_model()


class Command(BaseCommand):
    help = 'Set up Wazo extensions for all users in a tenant'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, required=True,
                          help='Tenant ID to set up extensions for')
        parser.add_argument('--start-ext', type=int, default=1001,
                          help='Starting extension number (default: 1001)')
        parser.add_argument('--caller-id', type=str, default='',
                          help='Default caller ID for outbound calls')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without making changes')

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        start_ext = options['start_ext']
        caller_id = options['caller_id']
        dry_run = options['dry_run']
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Setting up Wazo Extensions")
        self.stdout.write("=" * 50 + "\n")
        
        # Get tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            self.stdout.write(f"Tenant: {tenant.name}")
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant {tenant_id} not found"))
            return
        
        # Get users without extensions
        users = User.objects.filter(tenant=tenant).exclude(
            wazo_extension__isnull=False
        )
        
        self.stdout.write(f"Found {users.count()} users without extensions\n")
        
        if users.count() == 0:
            self.stdout.write(self.style.SUCCESS("All users already have extensions!"))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made\n"))
        
        created = 0
        for i, user in enumerate(users):
            ext = str(start_ext + i)
            
            if dry_run:
                self.stdout.write(f"  Would create: {user.email} → Ext {ext}")
            else:
                try:
                    WazoExtension.objects.create(
                        tenant=tenant,
                        user=user,
                        extension=ext,
                        caller_id=caller_id,
                        is_active=True
                    )
                    self.stdout.write(self.style.SUCCESS(f"  Created: {user.email} → Ext {ext}"))
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Failed: {user.email} - {e}"))
        
        self.stdout.write("\n" + "=" * 50)
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Created {created} extensions"))
        else:
            self.stdout.write(f"Would create {users.count()} extensions")
        self.stdout.write("=" * 50 + "\n")
