# File: /home/silaskimani/Documents/replit/git/salescompass/core/tenants/management/commands/check_overages.py
from django.core.management.base import BaseCommand
from tenants.models import Tenant
from tenants.views import OverageAlertService

class Command(BaseCommand):
    help = 'Check for usage overages and create alerts'

    def handle(self, *args, **options):
        # Get all active tenants
        tenants = Tenant.objects.filter(is_active=True)
        
        total_alerts = 0
        for tenant in tenants:
            alerts = OverageAlertService.check_usage_thresholds(tenant)
            total_alerts += len(alerts)
            
            if alerts:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {len(alerts)} overage alert(s) for tenant "{tenant.name}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully checked overages, created {total_alerts} alerts')
        )