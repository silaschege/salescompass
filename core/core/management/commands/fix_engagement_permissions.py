"""
Django management command to add engagement:read permission to Sales Rep and Support Agent roles.

Usage:
    python manage.py fix_engagement_permissions
"""

from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Add engagement:read permission to Sales Rep and Support Agent roles'

    def handle(self, *args, **kwargs):
        updated_count = 0
        
        # Update Sales Rep roles
        sales_roles = Role.objects.filter(name='Sales Rep')
        for role in sales_roles:
            if 'engagement:read' not in role.permissions:
                role.permissions.append('engagement:read')
                role.save(update_fields=['permissions'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Added engagement:read to Sales Rep role (tenant_id={role.tenant_id})')
                )
        
        # Update Support Agent roles
        support_roles = Role.objects.filter(name='Support Agent')
        for role in support_roles:
            if 'engagement:read' not in role.permissions:
                role.permissions.append('engagement:read')
                role.save(update_fields=['permissions'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Added engagement:read to Support Agent role (tenant_id={role.tenant_id})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} role(s)!')
        )
