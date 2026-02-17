import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import TenantRole, TenantTerritory, TenantMember
# Ensure we can import from legacy modules even if models are deleted
try:
    from accounts.models import TeamRole, Territory, OrganizationMember
except (ImportError, RuntimeError):
    TeamRole = Territory = OrganizationMember = None

try:
    from settings_app.models import TeamMember as LegacyTeamMember
except (ImportError, RuntimeError):
    LegacyTeamMember = None

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrates organization data (roles, territories, members) to the tenants module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the migration without saving changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No actual changes will be made."))

        try:
            with transaction.atomic():
                self.migrate_roles()
                self.migrate_territories()
                self.migrate_members()
                
                if dry_run:
                    self.stdout.write(self.style.WARNING("Dry run completed successfully. Rolling back transactions."))
                    raise Exception("Dry run rollback")
                    
            self.stdout.write(self.style.SUCCESS("Organization data migration completed successfully."))
            
        except Exception as e:
            if str(e) == "Dry run rollback":
                pass
            else:
                self.stdout.write(self.style.ERROR(f"Migration failed: {str(e)}"))
                logger.exception("Migration failed")

    def migrate_roles(self):
        self.stdout.write("Migrating roles...")
        if not TeamRole:
            self.stdout.write(self.style.WARNING("TeamRole model not found, skipping."))
            return
        old_roles = TeamRole.objects.all()
        count = 0
        for old_role in old_roles:
            new_role, created = TenantRole.objects.get_or_create(
                tenant=old_role.tenant,
                name=old_role.role_name,
                defaults={
                    'description': old_role.label,
                    'is_system_role': old_role.is_system,
                    'order': old_role.order,
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Migrated {count} roles."))

    def migrate_territories(self):
        self.stdout.write("Migrating territories...")
        if not Territory:
            self.stdout.write(self.style.WARNING("Territory model not found, skipping."))
            return
        old_territories = Territory.objects.all()
        count = 0
        for old_territory in old_territories:
            new_territory, created = TenantTerritory.objects.get_or_create(
                tenant=old_territory.tenant,
                name=old_territory.territory_name,
                defaults={
                    'description': old_territory.label,
                    'order': old_territory.order,
                    'is_active': old_territory.territory_is_active,
                    'country_codes': getattr(old_territory, 'country_codes', []),
                }
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Migrated {count} territories."))

    def migrate_members(self):
        self.stdout.write("Migrating organization members...")
        # Step 1: Migrate from accounts.OrganizationMember
        if not OrganizationMember:
            self.stdout.write(self.style.WARNING("OrganizationMember model not found, skipping."))
        else:
            old_members = OrganizationMember.objects.all()
            count = 0
        for old_member in old_members:
            # Map old role and territory models to new ones
            new_role = None
            if old_member.role_ref:
                new_role = TenantRole.objects.filter(
                    tenant=old_member.tenant,
                    name=old_member.role_ref.role_name
                ).first()
            
            new_territory = None
            if old_member.territory_ref:
                new_territory = TenantTerritory.objects.filter(
                    tenant=old_member.tenant,
                    name=old_member.territory_ref.territory_name
                ).first()
            
            # Create TenantMember
            new_member, created = TenantMember.objects.update_or_create(
                user=old_member.user,
                tenant=old_member.tenant,
                defaults={
                    'role': new_role,
                    'territory': new_territory,
                    'status': old_member.status,
                    'hire_date': old_member.hire_date,
                    'termination_date': old_member.termination_date,
                    'quota_amount': old_member.quota_amount,
                    'quota_period': old_member.quota_period,
                    'commission_rate': old_member.commission_rate,
                    'territory_performance_score': old_member.territory_performance_score,
                    'territory_quota_attainment': old_member.territory_quota_attainment,
                    'territory_conversion_rate': old_member.territory_conversion_rate,
                    'territory_revenue_contribution': old_member.territory_revenue_contribution,
                    'phone': getattr(old_member, 'phone', ''),
                }
            )
            if created:
                count += 1
        
            # Step 2: Linked managers (needs a second pass)
            for old_member in old_members:
                if old_member.manager:
                    try:
                        new_member = TenantMember.objects.get(user=old_member.user)
                        # Check if manager has a user
                        if old_member.manager.user:
                            new_manager = TenantMember.objects.get(user=old_member.manager.user)
                            new_member.manager = new_manager
                            new_member.save()
                    except TenantMember.DoesNotExist:
                        pass
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} organization members."))

        # Step 3: Handle LegacyTeamMember from settings_app if it exists
        if LegacyTeamMember:
            legacy_count = 0
            for legacy_member in LegacyTeamMember.objects.all():
                # Check if already migrated
                if not TenantMember.objects.filter(user=legacy_member.user).exists():
                    TenantMember.objects.create(
                        user=legacy_member.user,
                        tenant=legacy_member.tenant,
                        phone=getattr(legacy_member, 'phone', ''),
                        status='active' # Default for legacy
                    )
                    legacy_count += 1
            if legacy_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Migrated {legacy_count} legacy members from settings_app."))
