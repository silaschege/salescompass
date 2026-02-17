import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, Role
from tenants.models import Tenant
from billing.models import Plan, Subscription
from accounts.models import Account, Contact
from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from cases.models import Case
from tasks.models import Task

class Command(BaseCommand):
    help = 'Creates dummy data for 3 tenants and control plane scenarios'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')

        # 1. Ensure Plans Exist
        starter_plan, _ = Plan.objects.get_or_create(
            slug='starter',
            defaults={
                'name': 'Starter', 'tier': 'starter', 
                'price_monthly': 29.00, 'price_yearly': 290.00,
                'max_users': 5, 'max_leads': 100
            }
        )
        pro_plan, _ = Plan.objects.get_or_create(
            slug='pro',
            defaults={
                'name': 'Pro', 'tier': 'pro', 
                'price_monthly': 99.00, 'price_yearly': 990.00,
                'max_users': 20, 'max_leads': 1000
            }
        )
        enterprise_plan, _ = Plan.objects.get_or_create(
            slug='enterprise',
            defaults={
                'name': 'Enterprise', 'tier': 'enterprise', 
                'price_monthly': 299.00, 'price_yearly': 2990.00,
                'max_users': 100, 'max_leads': 10000
            }
        )

        # ==========================================
        # Tenant 1: Fully Setup (Acme Corp)
        # ==========================================
        self.stdout.write('Setting up Tenant 1: Acme Corp (Fully Setup)...')
        tenant1, created = Tenant.objects.get_or_create(
            name='Acme Corp',
            defaults={'domain': 'acme.com'}
        )
        
        # Subscription
        Subscription.objects.update_or_create(
            tenant_id=str(tenant1.id),
            defaults={
                'plan': enterprise_plan,
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=30)
            }
        )

        # Roles
        admin_role, _ = Role.objects.get_or_create(
            name='Admin', tenant_id=str(tenant1.id),
            defaults={'permissions': ['*']}
        )
        sales_role, _ = Role.objects.get_or_create(
            name='Sales Rep', tenant_id=str(tenant1.id),
            defaults={'permissions': ['accounts:*', 'leads:*', 'opportunities:*', 'tasks:*', 'engagement:read']}
        )
        support_role, _ = Role.objects.get_or_create(
            name='Support Agent', tenant_id=str(tenant1.id),
            defaults={'permissions': ['cases:*', 'accounts:read', 'engagement:read']}
        )

        # Users
        t1_admin, _ = User.objects.get_or_create(
            email='admin@acme.com',
            defaults={'username': 'admin@acme.com', 'role': admin_role, 'tenant_id': str(tenant1.id)}
        )
        t1_admin.set_password('password123')
        t1_admin.save()

        t1_sales, _ = User.objects.get_or_create(
            email='sales@acme.com',
            defaults={'username': 'sales@acme.com', 'role': sales_role, 'tenant_id': str(tenant1.id)}
        )
        t1_sales.set_password('password123')
        t1_sales.save()

        support_user = User.objects.create_user(
            username='support',
            email='support@acme.com',
            password='password123',
            role=support_role,
            tenant_id=str(tenant1.id)
        )
        self.stdout.write(f" created support user: {support_user.email}")

        # Create TeamMember records for all users
        from settings_app.models import TeamMember
        from datetime import date
        
        # Admin team member
        admin_member, _ = TeamMember.objects.get_or_create(
            user=t1_admin,
            defaults={
                'tenant_id': str(tenant1.id),
                'role': None,
                'manager': None,
                'territory': None,
                'phone': '+1-555-0001',
                'hire_date': date(2024, 1, 1),
                'status': 'active',
                'quota_amount': None,
                'quota_period': 'monthly'
            }
        )
        self.stdout.write(f" created team member for: {t1_admin.email}")
        
        # Sales team member
        sales_member, _ = TeamMember.objects.get_or_create(
            user=t1_sales,
            defaults={
                'tenant_id': str(tenant1.id),
                'role': None,
                'manager': admin_member,
                'territory': None,
                'phone': '+1-555-0002',
                'hire_date': date(2024, 1, 15),
                'status': 'active',
                'quota_amount': 100000,
                'quota_period': 'monthly'
            }
        )
        self.stdout.write(f" created team member for: {t1_sales.email}")
        
        # Support team member
        support_member, _ = TeamMember.objects.get_or_create(
            user=support_user,
            defaults={
                'tenant_id': str(tenant1.id),
                'role': None,
                'manager': admin_member,
                'territory': None,
                'phone': '+1-555-0003',
                'hire_date': date(2024, 2, 1),
                'status': 'active',
                'quota_amount': None,
                'quota_period': 'monthly'
            }
        )
        self.stdout.write(f" created team member for: {support_user.email}")
        
        # Assign support_user to t1_support for subsequent operations if needed
        t1_support = support_user

        # Data: Accounts
        for i in range(5):
            acc, _ = Account.objects.get_or_create(
                name=f'Customer {i+1}',
                tenant_id=str(tenant1.id),
                defaults={
                    'industry': 'tech',
                    'owner': t1_sales,
                    'status': 'customer'
                }
            )
            # Contact
            Contact.objects.get_or_create(
                email=f'contact{i}@customer{i+1}.com',
                account=acc,
                tenant_id=str(tenant1.id),
                defaults={'first_name': 'John', 'last_name': f'Doe {i}'}
            )
            # Opportunity
            stage, _ = OpportunityStage.objects.get_or_create(
                name='Qualification', tenant_id=str(tenant1.id), defaults={'order': 1}
            )
            Opportunity.objects.get_or_create(
                name=f'Deal {i+1}',
                account=acc,
                tenant_id=str(tenant1.id),
                defaults={
                    'amount': 10000 * (i+1),
                    'stage': stage,
                    'close_date': timezone.now().date() + timedelta(days=30),
                    'owner': t1_sales
                }
            )
            # Case
            Case.objects.get_or_create(
                subject=f'Issue {i+1}',
                account=acc,
                tenant_id=str(tenant1.id),
                defaults={
                    'description': 'Something is broken',
                    'owner': t1_support,
                    'status': 'new'
                }
            )

        # ==========================================
        # Tenant 2: New Tenant (Beta Inc) - Setup in CP, needs user setup
        # ==========================================
        self.stdout.write('Setting up Tenant 2: Beta Inc (New, Setup)...')
        tenant2, _ = Tenant.objects.get_or_create(
            name='Beta Inc',
            defaults={'domain': 'beta.com'}
        )
        
        Subscription.objects.update_or_create(
            tenant_id=str(tenant2.id),
            defaults={
                'plan': pro_plan,
                'status': 'trialing',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=14)
            }
        )

        # Only 1 Admin User, no roles configured yet (or default)
        t2_admin, _ = User.objects.get_or_create(
            email='admin@beta.com',
            defaults={'username': 'admin@beta.com', 'tenant_id': str(tenant2.id)}
        )
        t2_admin.set_password('password123')
        t2_admin.save()
        # No other data

        # ==========================================
        # Tenant 3: New Tenant (Gamma LLC) - Registered, Billing not setup
        # ==========================================
        self.stdout.write('Setting up Tenant 3: Gamma LLC (Registered, No Billing)...')
        tenant3, _ = Tenant.objects.get_or_create(
            name='Gamma LLC',
            defaults={'domain': 'gamma.com'}
        )
        
        Subscription.objects.update_or_create(
            tenant_id=str(tenant3.id),
            defaults={
                'plan': starter_plan,
                'status': 'incomplete', # Billing not setup
            }
        )

        t3_admin, _ = User.objects.get_or_create(
            email='admin@gamma.com',
            defaults={'username': 'admin@gamma.com', 'tenant_id': str(tenant3.id)}
        )
        t3_admin.set_password('password123')
        t3_admin.save()

        # ==========================================
        # Control Plane Tickets
        # ==========================================
        self.stdout.write('Setting up Control Plane Tickets...')
        cp_tenant, _ = Tenant.objects.get_or_create(
            name='Control Plane',
            defaults={'domain': 'admin.salescompass.com'}
        )
        
        cp_admin, _ = User.objects.get_or_create(
            email='superadmin@salescompass.com',
            defaults={'username': 'superadmin@salescompass.com', 'tenant_id': str(cp_tenant.id), 'is_superuser': True}
        )
        cp_admin.set_password('password123')
        cp_admin.save()

        # Create a dummy account to attach cases to in CP (since Case requires Account)
        cp_account, _ = Account.objects.get_or_create(
            name='Internal Operations',
            tenant_id=str(cp_tenant.id),
            defaults={'owner': cp_admin}
        )

        # Tickets for different issues
        tickets = [
            ('Billing Issue: Gamma LLC', 'Payment method failed for Gamma LLC setup.', 'billing', 'high'),
            ('Onboarding: Beta Inc', 'Beta Inc needs assistance with role configuration.', 'support', 'medium'),
            ('Invoice Generation', 'Generate monthly invoices for active tenants.', 'billing', 'medium'),
            ('System Alert: API Latency', 'High latency observed in region us-east-1.', 'engineering', 'critical'),
        ]

        for subject, desc, team, priority in tickets:
            Case.objects.get_or_create(
                subject=subject,
                tenant_id=str(cp_tenant.id),
                account=cp_account,
                defaults={
                    'description': desc,
                    'assigned_team': team,
                    'priority': priority,
                    'owner': cp_admin,
                    'status': 'new'
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created dummy data!'))
