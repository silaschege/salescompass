"""
SalesCompass Data Seeding Script

Creates comprehensive test data with:
- 5 tenants at different lifecycle stages
- 100 accounts per tenant with varying characteristics
- Related data across all applets (leads, opportunities, contacts, cases, etc.)

Usage:
    python manage.py seed_data
    
    Options:
    --tenants N     Number of tenants to create (default: 5)
    --accounts N    Number of accounts per tenant (default: 100)
    --clear         Clear existing seed data before creating new
    --progressive   Enable progressive progress reporting
    --batch-size N  Batch size for bulk operations (default: 1000)
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker

# Import models
from tenants.models import Tenant
from accounts.models import Account, Contact
from leads.models import Lead, LeadStatus, LeadSource
from opportunities.models import Opportunity, OpportunityStage
from billing.models import Plan, Subscription
from cases.models import Case
from tasks.models import Task
from products.models import Product, PricingTier, ProductBundle
from proposals.models import Proposal, ApprovalTemplate
from marketing.models import Campaign, EmailTemplate, LandingPage, CampaignStatus
from sales.models import Sale, SalesCommissionRule as SalesCommRule
from commissions.models import CommissionPlan, CommissionRule, UserCommissionPlan
from communication.models import NotificationTemplate, CommunicationHistory
from engagement.models import EngagementEvent, NextBestAction
from automation.models import Workflow, WorkflowAction, WorkflowTrigger
from learn.models import Category, Article, ArticleVersion, Course, Lesson
from reports.models import Report, ReportType

from nps.models import NpsSurvey,NpsResponse  # New addition
from dashboard.models import DashboardWidget,WidgetCategory  # New addition
from feature_flags.models import FeatureFlag  # New addition

User = get_user_model()
fake = Faker()

# Configuration constants
INDUSTRIES = ['tech', 'finance', 'healthcare', 'retail', 'manufacturing', 'education', 'energy', 'other', 'telecom', 'automotive', 'pharma']
ACCOUNT_TIERS = ['enterprise', 'pro', 'free', 'premium']
ACCOUNT_STATUSES = ['active', 'at_risk', 'churned', 'paused']
LEAD_STATUSES = [
    {'name': 'new', 'label': 'New', 'is_qualified': False, 'is_closed': False},
    {'name': 'contacted', 'label': 'Contacted', 'is_qualified': False, 'is_closed': False},
    {'name': 'qualified', 'label': 'Qualified', 'is_qualified': True, 'is_closed': False},
    {'name': 'proposal', 'label': 'Proposal Sent', 'is_qualified': True, 'is_closed': False},
    {'name': 'closed_won', 'label': 'Closed Won', 'is_qualified': True, 'is_closed': True},
    {'name': 'closed_lost', 'label': 'Closed Lost', 'is_qualified': False, 'is_closed': True},
]
OPPORTUNITY_STAGES = [
    {'name': 'prospecting', 'label': 'Prospecting', 'probability': 0.10, 'is_won': False, 'is_lost': False},
    {'name': 'qualification', 'label': 'Qualification', 'probability': 0.25, 'is_won': False, 'is_lost': False},
    {'name': 'needs_analysis', 'label': 'Needs Analysis', 'probability': 0.40, 'is_won': False, 'is_lost': False},
    {'name': 'value_proposition', 'label': 'Value Proposition', 'probability': 0.50, 'is_won': False, 'is_lost': False},
    {'name': 'proposal', 'label': 'Proposal', 'probability': 0.60, 'is_won': False, 'is_lost': False},
    {'name': 'negotiation', 'label': 'Negotiation', 'probability': 0.80, 'is_won': False, 'is_lost': False},
    {'name': 'closed_won', 'label': 'Closed Won', 'probability': 1.0, 'is_won': True, 'is_lost': False},
    {'name': 'closed_lost', 'label': 'Closed Lost', 'probability': 0.0, 'is_won': False, 'is_lost': True},
]
CASE_PRIORITIES = ['low', 'medium', 'high', 'urgent']
CASE_STATUSES = ['open', 'in_progress', 'resolved', 'closed', 'pending']

# Tenant configurations
TENANT_CONFIGS = [
    {
        'name': 'TechCorp Enterprise',
        'slug': 'techcorp-enterprise',
        'subdomain': 'techcorp',
        'subscription_status': 'active',
        'is_active': True,
        'is_suspended': False,
        'plan_type': 'enterprise',
        'description': 'Leading technology solutions provider'
    },
    {
        'name': 'StartupX Trial',
        'slug': 'startupx-trial',
        'subdomain': 'startupx',
        'subscription_status': 'trialing',
        'is_active': True,
        'is_suspended': False,
        'plan_type': 'starter',
        'description': 'Early-stage startup exploring solutions'
    },
    {
        'name': 'Suspended Corp',
        'slug': 'suspended-corp',
        'subdomain': 'suspendedco',
        'subscription_status': 'past_due',
        'is_active': False,
        'is_suspended': True,
        'plan_type': 'professional',
        'description': 'Company with payment issues'
    },
    {
        'name': 'SMB Solutions',
        'slug': 'smb-solutions',
        'subdomain': 'smbsolutions',
        'subscription_status': 'active',
        'is_active': True,
        'is_suspended': False,
        'plan_type': 'professional',
        'description': 'Small to medium business solutions'
    },
    {
        'name': 'NewCo Onboarding',
        'slug': 'newco-onboarding',
        'subdomain': 'newco',
        'subscription_status': 'trialing',
        'is_active': True,
        'is_suspended': False,
        'plan_type': 'starter',
        'description': 'Recently onboarded client'
    },
]


class Command(BaseCommand):
    help = 'Seed the database with comprehensive test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenants',
            type=int,
            default=5,
            help='Number of tenants to create'
        )
        parser.add_argument(
            '--accounts',
            type=int,
            default=100,
            help='Number of accounts per tenant'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seed data before creating new'
        )
        parser.add_argument(
            '--progressive',
            action='store_true',
            help='Enable progressive progress reporting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk operations (default: 1000)'
        )

    def handle(self, *args, **options):
        num_tenants = min(options['tenants'], len(TENANT_CONFIGS))
        num_accounts = options['accounts']
        progressive = options['progressive']
        batch_size = options['batch_size']
        
        if options['clear']:
            self.stdout.write('Clearing existing seed data...')
            self.clear_seed_data()
        
        self.stdout.write(f'Creating {num_tenants} tenants with {num_accounts} accounts each...')
        
        # Create plans first
        plans = self.create_plans()
        
        for i, config in enumerate(TENANT_CONFIGS[:num_tenants]):
            self.stdout.write(f'\n=== Creating Tenant {i+1}/{num_tenants}: {config["name"]} ===')
            
            tenant = self.create_tenant(config, plans)
            admin_user = self.create_admin_user(tenant, config)
            sales_users = self.create_sales_users(tenant, 5)
            
            # Create reference data for tenant
            lead_statuses = self.create_lead_statuses(tenant)
            lead_sources = self.create_lead_sources(tenant)
            opp_stages = self.create_opportunity_stages(tenant)
            
            # Create products for tenant
            products = self.create_products(tenant)
            
            # Create marketing data
            self.create_marketing_data(tenant, admin_user)
            
            # Create accounts and related data
            self.stdout.write(f'  Creating {num_accounts} accounts...')
            all_users = [admin_user] + sales_users
            
            # Process accounts in batches for better performance
            for j in range(0, num_accounts, batch_size):
                batch_end = min(j + batch_size, num_accounts)
                batch_accounts = []
                
                for k in range(j, batch_end):
                    if progressive and (k + 1) % 20 == 0:
                        self.stdout.write(f'    Progress: {k+1}/{num_accounts} accounts')
                    
                    owner = random.choice(all_users)
                    account = self.create_account(tenant, owner, k)
                    batch_accounts.append(account)
                    
                    # Create contacts for account
                    contacts = self.create_contacts(tenant, account, random.randint(2, 5))
                    
                    # Create leads for account
                    self.create_leads(tenant, account, owner, lead_statuses, lead_sources, random.randint(1, 4))
                    
                    # Create opportunities for account
                    opportunities = self.create_opportunities(tenant, account, owner, opp_stages, random.randint(1, 3))
                    
                    for opp in opportunities:
                        self.create_proposals(tenant, opp, owner)
                        # if opp.stage.is_won:
                        #     # Randomly pick a product for the sale
                        #     if products:
                        #         self.create_sales(tenant, opp, products, owner)
                    
                    # Create cases for account
                    self.create_cases(tenant, account, owner, random.randint(0, 2))
                    
                    # Create tasks
                    self.create_tasks(tenant, account, owner, random.randint(1, 3))

                    # Create engagement data
                    if contacts:
                        self.create_engagement_data(tenant, account, contacts, owner)
            
            # Create commissions
            if products:
                self.create_commission_data(tenant, products, sales_users)
            
            # Create communications
            self.create_communication_data(tenant, admin_user)
            
            # Create automation
            self.create_automation_data(tenant, admin_user)
            
            # Create learn data
            self.create_learn_data(tenant, admin_user)
            
            # Create reports
            self.create_reports_data(tenant, admin_user)
            
            # # Create dashboards
            # self.create_dashboard_data(tenant, admin_user)
            
            # Create NPS surveys and responses
            # self.create_nps_data(tenant, admin_user)
            
            # # Create system settings
            # self.create_system_settings(tenant, admin_user)
            
            # Create feature flags
            self.create_feature_flags(tenant)
            
            # Create subscription for tenant
            self.create_subscription(tenant, plans.get(config['plan_type']), admin_user)
            
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created seed data!'))
        self.stdout.write(f'   - {num_tenants} tenants')
        self.stdout.write(f'   - {num_tenants * num_accounts} accounts')
        self.stdout.write(f'   - Approximately {num_tenants * num_accounts * 3} contacts')
        self.stdout.write(f'   - Approximately {num_tenants * num_accounts * 2} leads')
        self.stdout.write(f'   - Approximately {num_tenants * num_accounts * 2} opportunities')
        self.stdout.write(f'   - Additional data for reports, dashboards, NPS, and system settings')

    def clear_seed_data(self):
        """Clear existing seeded data (preserves superusers)."""
        slugs = [c['slug'] for c in TENANT_CONFIGS]
        
        # 0. Break circular dependency: Tenant -> User (admin)
        Tenant.objects.filter(slug__in=slugs).update(tenant_admin=None)

        # 1. Feature flags
        FeatureFlag.objects.filter(tenant__slug__in=slugs).delete()


        # 3. Dashboards and widgets
        WidgetCategory.objects.filter(tenant__slug__in=slugs).delete()
        DashboardWidget.objects.filter(tenant__slug__in=slugs).delete()

        # 4. NPS data
        NpsResponse.objects.filter(tenant__slug__in=slugs).delete()
        NpsSurvey.objects.filter(tenant__slug__in=slugs).delete()

        # 5. Broadly applicable engagement and communication data
        EngagementEvent.objects.filter(tenant__slug__in=slugs).delete()
        NextBestAction.objects.filter(tenant__slug__in=slugs).delete()
        CommunicationHistory.objects.filter(tenant__slug__in=slugs).delete()
        NotificationTemplate.objects.filter(tenant__slug__in=slugs).delete()

        # 6. Automation
        WorkflowAction.objects.filter(tenant__slug__in=slugs).delete()
        WorkflowTrigger.objects.filter(tenant__slug__in=slugs).delete()
        Workflow.objects.filter(tenant__slug__in=slugs).delete()

        # 7. Learning Management
        ArticleVersion.objects.filter(tenant__slug__in=slugs).delete()
        Lesson.objects.filter(tenant__slug__in=slugs).delete()
        Course.objects.filter(tenant__slug__in=slgs).delete()
        Article.objects.filter(tenant__slug__in=slugs).delete()
        Category.objects.filter(tenant__slug__in=slugs).delete()

        # 8. Reports
        Report.objects.filter(tenant__slug__in=slugs).delete()
        ReportType.objects.filter(tenant__slug__in=slugs).delete()

        # 9. Commissions and Sales
        UserCommissionPlan.objects.filter(tenant__slug__in=slugs).delete()
        CommissionRule.objects.filter(tenant__slug__in=slgs).delete()
        CommissionPlan.objects.filter(tenant__slug__in=slgs).delete()
        Sale.objects.filter(tenant__slug__in=slugs).delete()
        
        # 10. CRM Core and Marketing
        Proposal.objects.filter(tenant__slug__in=slugs).delete()
        Campaign.objects.filter(tenant__slug__in=slugs).delete()
        CampaignStatus.objects.filter(tenant__slug__in=slugs).delete()
        EmailTemplate.objects.filter(tenant__slug__in=slugs).delete()
        Task.objects.filter(tenant__slug__in=slugs).delete()
        Case.objects.filter(tenant__slug__in=slugs).delete()
        Opportunity.objects.filter(tenant__slug__in=slgs).delete()
        Lead.objects.filter(tenant__slug__in=slgs).delete()
        Contact.objects.filter(tenant__slug__in=slgs).delete()
        Account.objects.filter(tenant__slug__in=slgs).delete()
        Product.objects.filter(tenant__slug__in=slgs).delete()
        
        # 11. Reference data that may be connected to leads/opportunities
        OpportunityStage.objects.filter(tenant__slug__in=slgs).delete()
        LeadStatus.objects.filter(tenant__slug__in=slgs).delete()
        LeadSource.objects.filter(tenant__slug__in=slgs).delete()
        
        # 12. Infrastructure (Billing, Users, Tenant)
        Subscription.objects.filter(tenant__slug__in=slgs).delete()
        User.objects.filter(tenant__slug__in=slgs).delete()
        Tenant.objects.filter(slug__in=slgs).delete()

    def create_plans(self):
        """Create billing plans."""
        plans = {}
        plan_configs = [
            {'name': 'Starter', 'price': Decimal('29.99'), 'key': 'starter', 'features': ['basic_support', 'limited_storage']},
            {'name': 'Professional', 'price': Decimal('99.99'), 'key': 'professional', 'features': ['priority_support', 'enhanced_storage', 'advanced_reporting']},
            {'name': 'Enterprise', 'price': Decimal('299.99'), 'key': 'enterprise', 'features': ['24_7_support', 'unlimited_storage', 'custom_integrations', 'dedicated_account_manager']},
        ]
        for config in plan_configs:
            plan, _ = Plan.objects.get_or_create(
                name=config['name'],
                defaults={
                    'price': config['price'],
                    'is_active': True,
                    'features': config['features']
                }
            )
            plans[config['key']] = plan
        return plans

    def create_tenant(self, config, plans):
        """Create a tenant with the given configuration."""
        tenant, created = Tenant.objects.get_or_create(
            slug=config['slug'],
            defaults={
                'name': config['name'],
                'subdomain': config['subdomain'],
                'subscription_status': config['subscription_status'],
                'is_active': config['is_active'],
                'is_suspended': config['is_suspended'],
                'plan': plans.get(config['plan_type']),
                'trial_end_date': timezone.now() + timedelta(days=14) if config['subscription_status'] == 'trialing' else None,
                'description': config.get('description', ''),
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created tenant: {tenant.name}')
        return tenant

    def create_admin_user(self, tenant, config):
        """Create admin user for tenant."""
        email = f'admin@{config["subdomain"]}.example.com'
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': f'{config["subdomain"]}_admin',
                'first_name': 'Admin',
                'last_name': config['name'].split()[0],
                'tenant': tenant,
                'is_staff': True,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            tenant.tenant_admin = user
            tenant.save()
        return user

    def create_sales_users(self, tenant, count):
        """Create sales users for a tenant."""
        users = []
        for i in range(count):
            email = f'sales{i+1}@{tenant.subdomain}.example.com'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': f'{tenant.subdomain}_sales{i+1}',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'tenant': tenant,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            users.append(user)
        return users

    def create_lead_statuses(self, tenant):
        """Create lead statuses for tenant."""
        statuses = {}
        for i, status_config in enumerate(LEAD_STATUSES):
            status, created = LeadStatus.objects.get_or_create(
                tenant=tenant,
                status_name=status_config['name'],
                defaults={
                    'label': status_config['label'],
                    'order': i,
                    'is_qualified': status_config['is_qualified'],
                    'is_closed': status_config['is_closed'],
                }
            )
            if not status.id:
                status.tenant = tenant
                status.status_name = status_config['name']
                status.label = status_config['label']
                status.order = i
                status.is_qualified = status_config['is_qualified']
                status.is_closed = status_config['is_closed']
                status.save()
            statuses[status_config['name']] = status
        return statuses

    def create_lead_sources(self, tenant):
        """Create lead sources for tenant."""
        sources = {}
        source_configs = [
            {'name': 'website', 'label': 'Website'},
            {'name': 'referral', 'label': 'Referral'},
            {'name': 'event', 'label': 'Trade Show/Event'},
            {'name': 'linkedin', 'label': 'LinkedIn'},
            {'name': 'cold_call', 'label': 'Cold Call'},
            {'name': 'partner', 'label': 'Partner'},
            {'name': 'advertising', 'label': 'Advertising'},
            {'name': 'content_marketing', 'label': 'Content Marketing'},
        ]
        for i, config in enumerate(source_configs):
            source, created = LeadSource.objects.get_or_create(
                tenant=tenant,
                source_name=config['name'],
                defaults={
                    'label': config['label'],
                    'order': i,
                }
            )
            if not source.id:
                source.tenant = tenant
                source.source_name = config['name']
                source.label = config['label']
                source.order = i
                source.save()
            sources[config['name']] = source
        return sources

    def create_opportunity_stages(self, tenant):
        """Create opportunity stages for tenant."""
        stages = {}
        for i, stage_config in enumerate(OPPORTUNITY_STAGES):
            stage, created = OpportunityStage.objects.get_or_create(
                tenant=tenant,
                opportunity_stage_name=stage_config['name'],
                defaults={
                    'order': i,
                    'probability': Decimal(str(stage_config['probability'] * 100)),  # Store as 0-100
                    'is_won': stage_config['is_won'],
                    'is_lost': stage_config['is_lost'],
                }
            )
            if not stage.id:
                stage.tenant = tenant
                stage.opportunity_stage_name = stage_config['name']
                stage.order = i
                stage.probability = Decimal(str(stage_config['probability'] * 100))
                stage.is_won = stage_config['is_won']
                stage.is_lost = stage_config['is_lost']
                stage.save()
            stages[stage_config['name']] = stage
        return stages

    def create_account(self, tenant, owner, index):
        """Create an account with realistic data."""
        industry = random.choice(INDUSTRIES)
        tier = random.choice(ACCOUNT_TIERS)
        status = random.choice(ACCOUNT_STATUSES)
        
        # Vary revenue based on tier
        revenue_ranges = {
            'enterprise': (10000000, 500000000),
            'premium': (5000000, 100000000),
            'pro': (1000000, 50000000),
            'free': (100000, 5000000),
        }
        revenue_range = revenue_ranges.get(tier, (100000, 10000000))
        
        # Vary employee count based on tier
        employee_ranges = {
            'enterprise': (1000, 50000),
            'premium': (500, 5000),
            'pro': (100, 1000),
            'free': (10, 100),
        }
        employee_range = employee_ranges.get(tier, (10, 500))
        
        account = Account.objects.create(
            tenant=tenant,
            account_name=fake.company(),
            industry=industry,
            website=fake.url(),
            phone=fake.phone_number()[:50],
            country=fake.country()[:100],
            billing_address_line1=fake.street_address(),
            billing_city=fake.city(),
            billing_state=fake.state_abbr(),
            billing_postal_code=fake.postcode(),
            annual_revenue=Decimal(str(random.randint(*revenue_range))),
            number_of_employees=random.randint(*employee_range),
            tier=tier,
            status=status,
            health_score=Decimal(str(random.randint(20, 100))),
            owner=owner,
            is_active=True,
            created_at=timezone.now() - timedelta(days=random.randint(0, 730))  # Up to 2 years ago
        )
        return account

    def create_contacts(self, tenant, account, count):
        """Create contacts for an account."""
        contacts = []
        roles = ['CEO', 'CTO', 'CFO', 'VP of Sales', 'Director', 'Manager', 'Engineer', 'Analyst', 'Marketing Manager', 'Operations Director']
        
        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            unique_suffix = f'{account.id}_{i}'
            email = f'{first_name.lower()}.{last_name.lower()}.{unique_suffix}@{fake.domain_name()}'
            
            contact = Contact.objects.create(
                tenant=tenant,
                account=account,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=fake.phone_number()[:20],
                role=random.choice(roles),
                is_primary=i == 0,
                created_at=timezone.now() - timedelta(days=random.randint(0, 365))
            )
            contacts.append(contact)
        return contacts

    def create_leads(self, tenant, account, owner, statuses, lead_sources, count):
        """Create leads for an account."""
        leads = []
        status_names = list(statuses.keys())
        
        for i in range(count):
            status_name = random.choice(status_names)
            first_name = fake.first_name()
            last_name = fake.last_name()
            unique_suffix = f'{account.id}_{i}'
            email = f'{first_name.lower()}.{last_name.lower()}.lead.{unique_suffix}@example.com'
            
            # Randomly pick a source
            source_name = random.choice(list(lead_sources.keys()))
            source = lead_sources[source_name]

            lead = Lead.objects.create(
                tenant=tenant,
                account=account,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=fake.phone_number()[:20],
                company=account.account_name,
                industry=account.industry,
                job_title=fake.job()[:100],
                lead_source=source_name,
                source_ref=source,
                status=status_name,
                status_ref=statuses[status_name],
                lead_score=random.randint(10, 100),
                owner=owner,
                company_size=random.randint(10, 5000),
                annual_revenue=account.annual_revenue,
                created_at=timezone.now() - timedelta(days=random.randint(0, 180))
            )
            leads.append(lead)
        return leads

    def create_opportunities(self, tenant, account, owner, stages, count):
        """Create opportunities for an account."""
        opportunities = []
        stage_names = list(stages.keys())
        
        for _ in range(count):
            stage_name = random.choice(stage_names)
            stage = stages[stage_name]
            
            # Amount varies by stage
            base_amount = random.randint(10000, 500000)
            
            # Calculate dates
            close_date = timezone.now().date() + timedelta(days=random.randint(7, 180))
            expected_closing_date = close_date + timedelta(days=random.randint(-7, 7))
            
            # Probability should be a float 0.0-1.0
            probability = float(stage.probability) / 100.0 if stage.probability else 0.0
            
            opp = Opportunity.objects.create(
                tenant=tenant,
                account=account,
                opportunity_name=f'{account.account_name} - {fake.bs().title()[:50]}',
                amount=Decimal(str(base_amount)),
                stage=stage,
                close_date=close_date,
                expected_closing_date=expected_closing_date,
                probability=probability,
                owner=owner,
                created_at=timezone.now() - timedelta(days=random.randint(0, 180))
            )
            opportunities.append(opp)
        return opportunities

    def create_cases(self, tenant, account, owner, count):
        """Create support cases for an account."""
        cases = []
        
        for _ in range(count):
            case = Case.objects.create(
                tenant=tenant,
                account=account,
                subject=fake.sentence(nb_words=6)[:255],
                case_description=fake.paragraph(nb_sentences=3),
                priority=random.choice(CASE_PRIORITIES),
                status=random.choice(CASE_STATUSES),
                owner=owner,
                created_at=timezone.now() - timedelta(days=random.randint(0, 90))
            )
            cases.append(case)
        return cases

    def create_tasks(self, tenant, account, owner, count):
        """Create tasks for an account."""
        tasks = []
        task_types = ['follow_up', 'call', 'email', 'meeting', 'demo', 'custom']
        
        for _ in range(count):
            due_date = timezone.now() + timedelta(days=random.randint(-7, 30))
            task_type = random.choice(task_types)
            
            task = Task.objects.create(
                tenant=tenant,
                account=account,
                title=f'{task_type.replace("_", " ").title()}: {account.account_name}'[:255],
                task_description=fake.sentence(nb_words=10),
                assigned_to=owner,
                priority=random.choice(['low', 'medium', 'high']),
                status='completed' if due_date < timezone.now() else random.choice(['todo', 'in_progress']),
                due_date=due_date,
                task_type=task_type,
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            tasks.append(task)
        return tasks

    def create_subscription(self, tenant, plan, admin_user):
        """Create subscription for tenant."""
        if not plan:
            return None
        
        subscription, _ = Subscription.objects.get_or_create(
            tenant=tenant,
            defaults={
                'subscription_plan': plan,
                'user': admin_user,
                'subscription_is_active': tenant.is_active,
                'start_date': timezone.now() - timedelta(days=random.randint(30, 365)),
                'end_date': timezone.now() + timedelta(days=random.randint(30, 365)),
            }
        )
        return subscription

    def create_products(self, tenant):
        prods = []
        items = [
            ('Core Platforms', 'SaaS subscription for core features', 'CORE-001', 1500.00),
            ('AI Add-on', 'Advanced analytics and predictions', 'AI-X-001', 500.00),
            ('Security Suite', 'Enhanced encryption and audit logs', 'SEC-PRO', 800.00),
            ('Premium Support', 'Priority support and dedicated account manager', 'SUP-PREM', 300.00),
            ('Advanced Reporting', 'Detailed analytics and reporting tools', 'REPORT-ADV', 200.00),
            ('Custom Integration', 'Custom integration services', 'INT-CUST', 1000.00)
        ]
        for name, desc, sku_base, price in items:
            # Make SKU unique across tenants
            sku = f"{sku_base}-{tenant.slug[:10]}"
            p, _ = Product.objects.get_or_create(
                tenant=tenant, sku=sku,
                defaults={'product_name': name, 'product_description': desc, 'base_price': Decimal(price), 'pricing_model': 'flat'}
            )
            prods.append(p)
        return prods

    def create_sales(self, tenant, opportunity, products, owner):
        if not products:
            return
        product = random.choice(products)
        # Verify that all referenced objects exist and belong to the correct tenant
        if (not hasattr(opportunity, 'account') or 
            not opportunity.account or 
            opportunity.account.tenant_id != tenant.id):
            return  # Skip if account doesn't exist or belongs to different tenant
        
        if (not product or product.tenant_id != tenant.id):
            return  # Skip if product doesn't exist or belongs to different tenant
            
        if (not owner or owner.tenant_id != tenant.id):
            return  # Skip if owner doesn't exist or belongs to different tenant
        
        Sale.objects.create(
            tenant=tenant, account=opportunity.account,
            product=product, sales_rep=owner,
            amount=opportunity.amount
        )

    def create_proposals(self, tenant, opp, owner):
        Proposal.objects.create(
            tenant=tenant, opportunity=opp,
            title=f"Proposal for {opp.opportunity_name}",
            content="<h1>Executive Summary</h1><p>Proposed solution based on your requirements.</p>",
            status=random.choice(['draft', 'sent', 'viewed', 'accepted'])
        )

    def create_marketing_data(self, tenant, owner):
        status_ref, _ = CampaignStatus.objects.get_or_create(tenant=tenant, status_name='active', defaults={'label': 'Active'})
        c = Campaign.objects.create(
            tenant=tenant, owner=owner,
            campaign_name=f"{tenant.name} Q1 Growth Campaign",
            status_ref=status_ref,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=90),
            budget=Decimal('10000.00'),
            campaign_is_active=True
        )
        EmailTemplate.objects.create(
            tenant=tenant, template_name="Welcome Email", 
            subject="Welcome to SalesCompass", 
            content="<p>Hello world</p>",
            template_is_active=True
        )
        return [c]

    def create_commission_data(self, tenant, products, sales_users):
        plan = CommissionPlan.objects.create(tenant=tenant, commission_plan_name="Standard Sales Plan", basis='revenue', period='monthly')
        for prod in products:
            CommissionRule.objects.create(tenant=tenant, commission_rule_plan=plan, product=prod, rate_type='percentage', rate_value=Decimal('5.00'))
        
        for user in sales_users:
            UserCommissionPlan.objects.get_or_create(
                tenant=tenant, user=user, assigned_plan=plan, 
                defaults={'start_date': timezone.now().date()}
            )

    def create_communication_data(self, tenant, owner):
        tpl = NotificationTemplate.objects.create(
            tenant=tenant, name="Account Alert", template_type='email',
            subject="Critical Update", body_html="<p>An update has occurred.</p>",
            created_by=owner
        )
        CommunicationHistory.objects.create(
            tenant=tenant, communication_type='email', direction='outbound',
            recipient="test@example.com", subject="Test Communication",
            content_html="<p>Test Content</p>", status='sent', template_used=tpl,
            created_at=timezone.now() - timedelta(days=random.randint(0, 30))
        )

    def create_engagement_data(self, tenant, account_company, contacts, owner):
        if not contacts:
            return
        contact = random.choice(contacts)
        EngagementEvent.objects.create(
            tenant=tenant, account_company=account_company, account=owner, contact=contact,
            event_type='email_opened', title="Email Opened",
            description=f"{contact.first_name} opened the proposal email.",
            priority='high', engagement_score=15.0,
            created_at=timezone.now() - timedelta(days=random.randint(0, 30))
        )
        NextBestAction.objects.create(
            tenant=tenant, account=owner, contact=contact,
            action_type='schedule_call', description="Schedule follow-up call after proposal view",
            due_date=timezone.now() + timedelta(days=2), assigned_to=owner
        )

    def create_automation_data(self, tenant, owner):
        wf = Workflow.objects.create(
            tenant=tenant, created_by=owner,
            workflow_name="New Lead Welcome",
            workflow_trigger_type="lead.created",
            workflow_is_active=True
        )
        WorkflowAction.objects.create(
            tenant=tenant, workflow=wf,
            workflow_action_type="send_email",
            workflow_action_parameters={"template_id": 1},
            workflow_action_order=1
        )

    def create_learn_data(self, tenant, owner):
        cat, _ = Category.objects.get_or_create(tenant=tenant, category_name="Product Guides")
        art = Article.objects.create(
            tenant=tenant, title=f"Getting Started with {tenant.name}",
            article_slug=f"getting-started-{tenant.slug}-{random.randint(1000, 9999)}", category=cat,
            article_type="user_guide", status="published", author=owner
        )
        ArticleVersion.objects.create(tenant=tenant, article=art, content="## Welcome\nThis is the guide.", is_current=True)
        
        # Generate unique course title to avoid unique constraint failure
        course_title = f"Onboarding 101 - {tenant.name} - {random.randint(10000, 99999)}"
        course = Course.objects.create(
            tenant=tenant, 
            title=course_title, 
            slug=f"onboarding-101-{tenant.slug}-{random.randint(10000, 99999)}", 
            category=cat, 
            status="published", 
            author=owner
        )
        Lesson.objects.create(
            tenant=tenant, 
            course=course, 
            title="Welcome to the team", 
            slug=f"welcome-lesson-{tenant.slug}-{random.randint(10000, 99999)}", 
            content="Content here", 
            order_in_course=1, 
            article=art
        )
    def create_reports_data(self, tenant, owner):
        rtype, _ = ReportType.objects.get_or_create(tenant=tenant, type_name='sales_performance', defaults={'label': 'Sales Performance'})
        Report.objects.create(
            tenant=tenant, report_name="Monthly Sales Dashboard",
            report_type="sales_performance", report_type_ref=rtype,
            query_config={"metrics": ["revenue", "deals"]},
            created_by=owner
        )


    # def create_dashboard_data(self, tenant, owner):
    #     """Create dashboard and widget data for the tenant."""
    #     # Create a widget category first
    #     widget_category, _ = WidgetCategory.objects.get_or_create(
    #         tenant=tenant,
    #         category_name='general',
    #         defaults={
    #             'label': 'General Widgets',
    #             'order': 0,
    #             'widget_category_is_active': True
    #         }
    #     )
        
    #     # Create various dashboard widgets with unique widget_type_old values per tenant
    #     widgets_data = [
    #         {'widget_name': 'Revenue Chart', 'widget_type_old': f'revenue_chart_{tenant.slug}', 'position_x': 0, 'position_y': 0, 'width': 6, 'height': 4},
    #         {'widget_name': 'Opportunities Pipeline', 'widget_type_old': f'pipeline_{tenant.slug}', 'position_x': 6, 'position_y': 0, 'width': 6, 'height': 4},
    #         {'widget_name': 'Top Accounts', 'widget_type_old': f'top_accounts_{tenant.slug}', 'position_x': 0, 'position_y': 4, 'width': 6, 'height': 4},
    #         {'widget_name': 'Recent Activity', 'widget_type_old': f'recent_activity_{tenant.slug}', 'position_x': 6, 'position_y': 4, 'width': 6, 'height': 4},
    #     ]
        
    #     for widget_data in widgets_data:
    #         DashboardWidget.objects.create(
    #             tenant=tenant,
    #             widget_type_old=widget_data['widget_type_old'],
    #             widget_name=widget_data['widget_name'],
    #             widget_description=f"Dashboard widget for {widget_data['widget_name']}",
    #             category_old='general',
    #             template_path=f"dashboard/widgets/{widget_data['widget_type_old'].split('_')[0]}.html",  # Extract basic type for template path
    #             position='main',
    #             order=widget_data['position_x'],  # Using position_x as order
    #             widget_is_active=True
    #         )


    # def create_nps_data(self, tenant, owner):
    #     """Create NPS survey and response data."""
    #     survey = NpsSurvey.objects.create(
    #         tenant=tenant,
    #         nps_survey_name="Quarterly Customer Satisfaction Survey",
    #         nps_survey_description="How likely are you to recommend our service?",
    #         nps_survey_is_active=True
    #     )
        
    #     # Create some NPS responses
    #     for _ in range(20):
    #         NpsResponse.objects.create(
    #             tenant=tenant,
    #             survey=survey,
    #             score=random.randint(0, 10),
    #             comment=fake.paragraph(nb_sentences=1) if random.choice([True, False]) else "",
    #             contact_email=fake.email()
    #         )

    def create_feature_flags(self, tenant):
        """Create feature flags for the tenant."""
        flags = [
            {'name': 'enable_new_ui', 'is_enabled': True, 'description': 'Enable new user interface'},
            {'name': 'enable_advanced_analytics', 'is_enabled': False, 'description': 'Enable advanced analytics features'},
            {'name': 'enable_api_access', 'is_enabled': True, 'description': 'Enable API access for tenant'},
            {'name': 'enable_custom_reports', 'is_enabled': True, 'description': 'Enable custom report builder'},
            {'name': 'enable_mobile_app', 'is_enabled': False, 'description': 'Enable mobile application access'},
        ]
        
        for flag in flags:
            FeatureFlag.objects.get_or_create(
                tenant=tenant,
                name=flag['name'],
                defaults={
                    'is_enabled': flag['is_enabled'],
                    'description': flag['description']
                }
            )