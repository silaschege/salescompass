from django.core.management.base import BaseCommand
from core.models import User
from access_control.role_models import Role
from tenants.models import Tenant

class Command(BaseCommand):
    help = 'Assign default roles to users based on their tenant and status'

    def handle(self, *args, **options):
        users = User.objects.all()
        assigned_count = 0
        
        for user in users:
            if user.role:
                continue
                
            if user.is_superuser:
                # System-wide roles could be used here if needed, but for now
                # superusers often act as Tenant Admins for the primary tenant
                continue
                
            if user.tenant:
                # Assign 'Tenant Admin' if user is staff or it's the only user
                role_name = 'Tenant Admin' if user.is_staff or user.tenant.users.count() == 1 else 'Standard User'
                
                try:
                    role = Role.objects.get(name=role_name, tenant=user.tenant)
                    user.role = role
                    user.save(update_fields=['role'])
                    assigned_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Assigned role '{role_name}' to user {user.email} in tenant {user.tenant.name}"))
                except Role.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Role '{role_name}' not found for tenant {user.tenant.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {user.email} has no tenant association. Skipping role assignment."))

        self.stdout.write(self.style.SUCCESS(f"Successfully assigned roles to {assigned_count} users."))
