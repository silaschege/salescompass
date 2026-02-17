from django.core.management.base import BaseCommand
from hr.models import Employee
from hr.services import LeaveAccrualService
from tenants.models import Tenant

class Command(BaseCommand):
    help = 'Triggers leave accruals for all tenants or a specific tenant.'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, help='ID of the tenant to run accruals for')

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        
        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id)
        else:
            tenants = Tenant.objects.all()

        for tenant in tenants:
            self.stdout.write(f"Running leave accruals for tenant: {tenant.name}")
            results = LeaveAccrualService.run_accruals(tenant)
            self.stdout.write(self.style.SUCCESS(f"Processed {len(results)} accrual items for {tenant.name}"))
