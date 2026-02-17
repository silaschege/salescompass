import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
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

User = get_user_model()
fake = Faker()

STARTUPX_CONFIG = {
    'name': 'StartupX Trial',
    'slug': 'startupx-trial',
    'subdomain': 'startupx',
    'subscription_status': 'trialing',
    'is_active': True,
    'is_suspended': False,
    'plan_type': 'starter',
}

INDUSTRIES = ['SaaS', 'FinTech', 'HealthTech', 'E-commerce', 'AI/ML', 'CleanEnergy']
LEAD_STATUSES = [
    {'name': 'new', 'label': 'New', 'is_qualified': False, 'is_closed': False},
    {'name': 'contacted', 'label': 'Contacted', 'is_qualified': False, 'is_closed': False},
    {'name': 'qualified', 'label': 'Qualified', 'is_qualified': True, 'is_closed': False},
    {'name': 'proposal', 'label': 'Proposal Sent', 'is_qualified': True, 'is_closed': False},
    {'name': 'closed_won', 'label': 'Closed Won', 'is_qualified': True, 'is_closed': True},
    {'name': 'closed_lost', 'label': 'Closed Lost', 'is_qualified': False, 'is_closed': True},
]
OPPORTUNITY_STAGES = [
    {'name': 'prospecting', 'label': 'Prospecting', 'probability': 10, 'is_won': False, 'is_lost': False},
    {'name': 'qualification', 'label': 'Qualification', 'probability': 25, 'is_won': False, 'is_lost': False},
    {'name': 'proposal', 'label': 'Proposal', 'probability': 65, 'is_won': False, 'is_lost': False},
    {'name': 'negotiation', 'label': 'Negotiation', 'probability': 85, 'is_won': False, 'is_lost': False},
    {'name': 'closed_won', 'label': 'Closed Won', 'probability': 100, 'is_won': True, 'is_lost': False},
    {'name': 'closed_lost', 'label': 'Closed Lost', 'probability': 0, 'is_won': False, 'is_lost': True},
]

class Command(BaseCommand):
    help = 'Seed StartupX Trial tenant with comprehensive data across all applets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing StartupX Trial data before creating new'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🚀 Starting StartupX Trial Seeding...'))
        
        if options['clear']:
            self.stdout.write('Clearing existing StartupX Trial data...')
            self.clear_startupx_data()

        # 1. Platform Foundation
        plans = self.create_plans()
        tenant = self.create_tenant(STARTUPX_CONFIG, plans)
        admin_user = self.create_admin_user(tenant, STARTUPX_CONFIG)
        sales_users = self.create_sales_users(tenant, 3)
        all_users = [admin_user] + sales_users
        
        # 2. CRM Core Reference Data
        lead_statuses = self.create_lead_statuses(tenant)
        lead_sources = self.create_lead_sources(tenant)
        opp_stages = self.create_opportunity_stages(tenant)
        
        # 3. Products & Finance
        products = self.create_products(tenant)
        self.create_subscription(tenant, plans['starter'], admin_user)
        
        # 4. Marketing
        campaigns = self.create_marketing_data(tenant, admin_user)
        
        # 5. Accounts & Contacts
        self.stdout.write('Creating Accounts and related CRM data...')
        for i in range(10):  # 10 comprehensive accounts
            owner = random.choice(all_users)
            account = self.create_account(tenant, owner)
            contacts = self.create_contacts(tenant, account, random.randint(1, 3))
            
            # Leads
            self.create_leads(tenant, account, owner, lead_statuses, lead_sources, random.randint(1, 3))
            
            # Opportunities & Proposals
            opportunities = self.create_opportunities(tenant, account, owner, opp_stages, random.randint(1, 2))
            for opp in opportunities:
                self.create_proposals(tenant, opp, owner)
                if opp.stage.is_won:
                    self.create_sales(tenant, opp, products, owner)
            
            # Support Cases
            self.create_cases(tenant, account, owner, random.randint(0, 2))
            
            # Tasks
            self.create_tasks(tenant, account, owner, random.randint(2, 5))
            
            # Engagement
            self.create_engagement_data(tenant, account, contacts, owner)
            
        # 6. Commissions
        self.create_commission_data(tenant, products, sales_users)
        
        # 7. Communications
        self.create_communication_data(tenant, admin_user)
        
        # 8. Automation
        self.create_automation_data(tenant, admin_user)
        
        # 9. Learn (LMS)
        self.create_learn_data(tenant, admin_user)
        
        # 10. Reports
        self.create_reports_data(tenant, admin_user)

        self.stdout.write(self.style.SUCCESS('\n✨ StartupX Trial Seeding Completed successfully!'))

    def clear_startupx_data(self):
        """Clear existing StartupX Trial data."""
        slug = STARTUPX_CONFIG['slug']
        # Clear in reverse dependency order
        EngagementEvent.objects.filter(tenant__slug=slug).delete()
        NextBestAction.objects.filter(tenant__slug=slug).delete()
        CommunicationHistory.objects.filter(tenant__slug=slug).delete()
        WorkflowAction.objects.filter(tenant__slug=slug).delete()
        WorkflowTrigger.objects.filter(tenant__slug=slug).delete()
        Workflow.objects.filter(tenant__slug=slug).delete()
        ArticleVersion.objects.filter(tenant__slug=slug).delete()
        Lesson.objects.filter(tenant__slug=slug).delete()
        Course.objects.filter(tenant__slug=slug).delete()
        Article.objects.filter(tenant__slug=slug).delete()
        Category.objects.filter(tenant__slug=slug).delete()
        Report.objects.filter(tenant__slug=slug).delete()
        CommissionRule.objects.filter(tenant__slug=slug).delete()
        CommissionPlan.objects.filter(tenant__slug=slug).delete()
        Sale.objects.filter(tenant__slug=slug).delete()
        Proposal.objects.filter(tenant__slug=slug).delete()
        Campaign.objects.filter(tenant__slug=slug).delete()
        Task.objects.filter(tenant__slug=slug).delete()
        Case.objects.filter(tenant__slug=slug).delete()
        Opportunity.objects.filter(tenant__slug=slug).delete()
        Lead.objects.filter(tenant__slug=slug).delete()
        Contact.objects.filter(tenant__slug=slug).delete()
        Account.objects.filter(tenant__slug=slug).delete()
        Product.objects.filter(tenant__slug=slug).delete()
        Subscription.objects.filter(tenant__slug=slug).delete()

    # --- Platform Foundation ---
    def create_plans(self):
        plans = {}
        for name, price in [('Starter', '29.99'), ('Pro', '99.99'), ('Enterprise', '299.99')]:
            plan, _ = Plan.objects.get_or_create(
                name=name,
                defaults={'price': Decimal(price), 'is_active': True}
            )
            plans[name.lower()] = plan
        return plans

    def create_tenant(self, config, plans):
        tenant, _ = Tenant.objects.get_or_create(
            slug=config['slug'],
            defaults={
                'name': config['name'],
                'subdomain': config['subdomain'],
                'subscription_status': config['subscription_status'],
                'is_active': config['is_active'],
                'plan': plans[config['plan_type']],
                'trial_end_date': timezone.now() + timedelta(days=14)
            }
        )
        return tenant

    def create_admin_user(self, tenant, config):
        username = f'{config["subdomain"]}_admin'
        email = f'admin@{config["subdomain"]}.example.com'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'StartupX',
                'last_name': 'Admin',
                'tenant': tenant,
                'is_staff': True,
            }
        )
        if created:
            user.set_password('StartupX123!')
            user.save()
            tenant.tenant_admin = user
            tenant.save()
        return user

    def create_sales_users(self, tenant, count):
        users = []
        for i in range(count):
            username = f'{tenant.subdomain}_sales{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'sales{i+1}@{tenant.subdomain}.example.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'tenant': tenant,
                }
            )
            if created:
                user.set_password('Sales123!')
                user.save()
            users.append(user)
        return users

    # --- CRM Core ---
    def create_lead_statuses(self, tenant):
        return {s['name']: LeadStatus.objects.get_or_create(tenant=tenant, status_name=s['name'], defaults={'label': s['label'], 'is_qualified': s['is_qualified'], 'is_closed': s['is_closed']})[0] for s in LEAD_STATUSES}

    def create_lead_sources(self, tenant):
        sources = ['Website', 'Referral', 'LinkedIn', 'Webinar', 'Partner']
        return {s: LeadSource.objects.get_or_create(tenant=tenant, source_name=s.lower(), defaults={'label': s})[0] for s in sources}

    def create_opportunity_stages(self, tenant):
        return {s['name']: OpportunityStage.objects.get_or_create(tenant=tenant, opportunity_stage_name=s['name'], defaults={'order': i, 'probability': Decimal(s['probability']), 'is_won': s['is_won'], 'is_lost': s['is_lost']})[0] for i, s in enumerate(OPPORTUNITY_STAGES)}

    def create_account(self, tenant, owner):
        return Account.objects.create(
            tenant=tenant, owner=owner,
            account_name=fake.company(),
            industry=random.choice(INDUSTRIES),
            status='active',
            health_score=random.randint(60, 100),
            annual_revenue=Decimal(random.randint(50000, 5000000)),
            number_of_employees=random.randint(10, 500)
        )

    def create_contacts(self, tenant, account, count):
        return [Contact.objects.create(tenant=tenant, account=account, first_name=fake.first_name(), last_name=fake.last_name(), email=fake.email(), is_primary=(i==0)) for i in range(count)]

    def create_leads(self, tenant, account, owner, statuses, sources, count):
        for i in range(count):
            Lead.objects.create(
                tenant=tenant, account=account, owner=owner,
                first_name=fake.first_name(), last_name=fake.last_name(),
                email=f"{fake.user_name()}{i}@example.com", company=account.account_name,
                status_ref=random.choice(list(statuses.values())),
                source_ref=random.choice(list(sources.values()))
            )

    def create_opportunities(self, tenant, account, owner, stages, count):
        opps = []
        for _ in range(count):
            stage = random.choice(list(stages.values()))
            opps.append(Opportunity.objects.create(
                tenant=tenant, account=account, owner=owner,
                opportunity_name=f"{account.account_name} - {fake.word().capitalize()} Solution",
                amount=Decimal(random.randint(5000, 100000)),
                stage=stage,
                probability=float(stage.probability) / 100.0,
                close_date=timezone.now().date() + timedelta(days=random.randint(30, 90))
            ))
        return opps

    # --- Products & Sales ---
    def create_products(self, tenant):
        prods = []
        items = [
            ('Core Platforms', 'SaaS subscription for core features', 'CORE-001', 1500.00),
            ('AI Add-on', 'Advanced analytics and predictions', 'AI-X-001', 500.00),
            ('Security Suite', 'Enhanced encryption and audit logs', 'SEC-PRO', 800.00)
        ]
        for name, desc, sku, price in items:
            p, _ = Product.objects.get_or_create(
                tenant=tenant, sku=sku,
                defaults={'product_name': name, 'product_description': desc, 'base_price': Decimal(price), 'pricing_model': 'flat'}
            )
            prods.append(p)
        return prods

    def create_sales(self, tenant, opportunity, products, owner):
        product = random.choice(products)
        Sale.objects.create(
            tenant=tenant, account=opportunity.account,
            product=product, sales_rep=owner,
            amount=opportunity.amount, sale_date=timezone.now()
        )

    def create_proposals(self, tenant, opp, owner):
        Proposal.objects.create(
            tenant=tenant, opportunity=opp,
            title=f"Proposal for {opp.opportunity_name}",
            content="<h1>Executive Summary</h1><p>Proposed solution based on your requirements.</p>",
            status=random.choice(['draft', 'sent', 'viewed', 'accepted'])
        )

    # --- Marketing ---
    def create_marketing_data(self, tenant, owner):
        status_ref, _ = CampaignStatus.objects.get_or_create(tenant=tenant, status_name='active', defaults={'label': 'Active'})
        c = Campaign.objects.create(
            tenant=tenant, owner=owner,
            campaign_name="StartupX Q1 Growth Campaign",
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

    # --- Commissions ---
    def create_commission_data(self, tenant, products, sales_users):
        plan = CommissionPlan.objects.create(tenant=tenant, commission_plan_name="Standard Sales Plan", basis='revenue', period='monthly')
        for prod in products:
            CommissionRule.objects.create(tenant=tenant, commission_rule_plan=plan, product=prod, rate_type='flat', rate_value=Decimal('10.00'))
        
        for user in sales_users:
            UserCommissionPlan.objects.create(tenant=tenant, user=user, assigned_plan=plan, start_date=timezone.now().date())

    # --- Communication ---
    def create_communication_data(self, tenant, owner):
        tpl = NotificationTemplate.objects.create(
            tenant=tenant, name="Account Alert", template_type='email',
            subject="Critical Update", body_html="<p>An update has occurred.</p>",
            created_by=owner
        )
        CommunicationHistory.objects.create(
            tenant=tenant, communication_type='email', direction='outbound',
            recipient="test@example.com", subject="Test Communication",
            content_html="<p>Test Content</p>", status='sent', template_used=tpl
        )

    # --- Engagement ---
    def create_engagement_data(self, tenant, account_company, contacts, owner):
        if not contacts:
            return
        contact = random.choice(contacts)
        EngagementEvent.objects.create(
            tenant=tenant, account_company=account_company, account=owner, contact=contact,
            event_type='email_opened', title="Email Opened",
            description=f"{contact.first_name} opened the proposal email.",
            priority='high', engagement_score=15.0
        )
        NextBestAction.objects.create(
            tenant=tenant, account=owner, contact=contact,
            action_type='schedule_call', description="Schedule follow-up call after proposal view",
            due_date=timezone.now() + timedelta(days=2), assigned_to=owner
        )

    # --- Automation ---
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

    # --- Learn ---
    def create_learn_data(self, tenant, owner):
        cat, _ = Category.objects.get_or_create(tenant=tenant, category_name="Product Guides")
        art = Article.objects.create(
            tenant=tenant, title="Getting Started with StartupX",
            article_slug=f"getting-started-{random.randint(1000, 9999)}", category=cat,
            article_type="user_guide", status="published", author=owner
        )
        ArticleVersion.objects.create(tenant=tenant, article=art, content="## Welcome\nThis is the guide.", is_current=True)
        
        course = Course.objects.create(tenant=tenant, title="Onboarding 101", slug=f"onboarding-101-{random.randint(1000, 9999)}", category=cat, status="published", author=owner)
        Lesson.objects.create(tenant=tenant, course=course, title="Welcome to the team", slug=f"welcome-lesson-{random.randint(1000, 9999)}", content="Content here", order_in_course=1, article=art)

    # --- Reports ---
    def create_reports_data(self, tenant, owner):
        rtype, _ = ReportType.objects.get_or_create(tenant=tenant, type_name='sales_performance', defaults={'label': 'Sales Performance'})
        Report.objects.create(
            tenant=tenant, report_name="Monthly Sales Dashboard",
            report_type="sales_performance", report_type_ref=rtype,
            query_config={"metrics": ["revenue", "deals"]},
            created_by=owner
        )

    # --- Tasks & Cases ---
    def create_tasks(self, tenant, account, owner, count):
        for _ in range(count):
            Task.objects.create(
                tenant=tenant, account=account, assigned_to=owner,
                title=f"Follow up with {account.account_name} - {fake.word()}",
                due_date=timezone.now() + timedelta(days=random.randint(1, 14)),
                priority=random.choice(['low', 'medium', 'high']),
                status='todo', task_type='custom'
            )

    def create_cases(self, tenant, account, owner, count):
        for _ in range(count):
            Case.objects.create(
                tenant=tenant, account=account, owner=owner,
                subject=fake.sentence(), priority=random.choice(['low', 'medium', 'high']),
                status='open'
            )

    def create_subscription(self, tenant, plan, owner):
        Subscription.objects.get_or_create(
            tenant=tenant,
            defaults={
                'subscription_plan': plan, 'user': owner,
                'subscription_is_active': True,
                'start_date': timezone.now() - timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=335)
            }
        )
