from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
import random
from datetime import timedelta
import uuid

# Models
from tenants.models import Tenant
from core.models import Role
from billing.models import Plan, Subscription
from settings_app.models import TeamRole, TeamMember, Territory, PipelineStage
from leads.models import Lead, LeadSource, LeadStatus
from opportunities.models import Opportunity, OpportunityStage, OpportunityProduct, WinLossAnalysis
from accounts.models import Account, Contact
from cases.models import Case, CaseComment, CsatSurvey, CsatResponse
from products.models import Product, PricingTier
from marketing.models import MarketingCampaign, EmailTemplate, CampaignRecipient, EmailCampaign
from proposals.models import Proposal, ProposalEvent, ProposalEmail
from communication.models import Call, Meeting, Email
from learn.models import Article, Category, ArticleVersion
from nps.models import NpsSurvey, NpsResponse
from commissions.models import CommissionPlan, CommissionRule, UserCommissionPlan, Commission

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulates an end-to-end flow of the SalesCompass CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing simulation data before starting',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting SalesCompass Simulation...'))

        if options['clean']:
            self.clean_data()

        try:
            with transaction.atomic():
                # Phase 1: Control Plane & Tenant Setup
                super_admin = self.setup_super_admin()
                tenant, admin_user = self.setup_tenant()
                
                # Phase 2: Team Setup
                sales_reps, support_agents = self.setup_team(tenant, admin_user)
                
                # Phase 3: Products & Marketing
                products = self.setup_products(tenant, admin_user)
                campaign = self.setup_marketing(tenant, admin_user)
                
                # Phase 4: Sales & Proposals
                accounts, opportunities = self.simulate_sales_workflow(tenant, sales_reps, products, campaign)
                
                # Phase 5: Support & Success
                self.simulate_support_workflow(tenant, support_agents, accounts)
                self.setup_customer_success(tenant, admin_user, accounts)
                
                # Phase 6: Commissions & Reporting
                self.simulate_commissions(tenant, admin_user, sales_reps, opportunities)
                self.simulate_reporting(tenant, admin_user)

                self.stdout.write(self.style.SUCCESS('Simulation Completed Successfully!'))
                self.print_summary(tenant)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Simulation Failed: {str(e)}'))
            import traceback
            traceback.print_exc()

    def clean_data(self):
        self.stdout.write('Cleaning old data...')
        Tenant.objects.filter(name="Acme Corp").delete()
        User.objects.filter(email__contains="@acme.com").delete()
        Role.objects.filter(name__startswith="Acme ").delete()
        TeamRole.objects.filter(name__startswith="Acme ").delete()
        # Clean up other related data if needed, but cascading might handle some

    def setup_super_admin(self):
        self.stdout.write('1. Setting up Super Admin...')
        user, created = User.objects.get_or_create(
            email='superadmin@salescompass.com',
            defaults={
                'username': 'superadmin@salescompass.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        return user

    def setup_tenant(self):
        self.stdout.write('2. Onboarding Tenant "Acme Corp"...')
        
        # Create Plan if not exists
        plan, _ = Plan.objects.get_or_create(
            name="Enterprise",
            defaults={
                'slug': 'enterprise',
                'tier': 'enterprise',
                'price_monthly': 999.00,
                'price_yearly': 9990.00,
                'max_users': 100,
                'max_leads': 10000
            }
        )

        # Create Tenant
        tenant, created = Tenant.objects.get_or_create(
            name="Acme Corp",
            defaults={
                'domain': 'acme.com',
                'plan': plan,
                'subscription_status': 'active'
            }
        )
        
        # Create Subscription
        Subscription.objects.get_or_create(
            tenant_id=tenant.id,
            defaults={
                'plan': plan,
                'status': 'active',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timedelta(days=365)
            }
        )

        # Create Admin Role
        admin_role, _ = Role.objects.get_or_create(
            name='Acme Admin',
            tenant_id=tenant.id,
            defaults={'permissions': ['*']}
        )

        # Create Tenant Admin
        admin_user, created = User.objects.get_or_create(
            email='admin@acme.com',
            defaults={
                'username': 'admin@acme.com',
                'tenant_id': tenant.id,
                'role': admin_role,
                'is_staff': True
            }
        )
        if created:
            admin_user.set_password('password123')
            admin_user.save()
            
        return tenant, admin_user

    def setup_team(self, tenant, admin_user):
        self.stdout.write('3. Setting up Team...')
        
        # Create Roles
        sales_role, _ = TeamRole.objects.get_or_create(
            name='Acme Sales Representative',
            tenant_id=tenant.id,
            defaults={'base_permissions': ['leads:read', 'leads:write', 'opportunities:read', 'opportunities:write']}
        )
        support_role, _ = TeamRole.objects.get_or_create(
            name='Acme Support Agent',
            tenant_id=tenant.id,
            defaults={'base_permissions': ['cases:read', 'cases:write', 'accounts:read']}
        )
        
        # Create Territory
        territory, _ = Territory.objects.get_or_create(
            name='north_america',
            tenant_id=tenant.id,
            defaults={'country_codes': ['US', 'CA']}
        )

        # Create Sales Reps
        sales_reps = []
        for i in range(1, 4):
            email = f'sales{i}@acme.com'
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'tenant_id': tenant.id,
                    'first_name': f'Sales',
                    'last_name': f'Rep {i}'
                }
            )
            user.set_password('password123')
            user.save()
            
            TeamMember.objects.get_or_create(
                user=user,
                defaults={
                    'role': sales_role,
                    'territory': territory,
                    'status': 'active',
                    'quota_amount': 50000.00,
                    'tenant_id': tenant.id
                }
            )
            sales_reps.append(user)

        # Create Support Agents
        support_agents = []
        for i in range(1, 3):
            email = f'support{i}@acme.com'
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'tenant_id': tenant.id,
                    'first_name': f'Support',
                    'last_name': f'Agent {i}'
                }
            )
            user.set_password('password123')
            user.save()
            
            TeamMember.objects.get_or_create(
                user=user,
                defaults={
                    'role': support_role,
                    'status': 'active',
                    'tenant_id': tenant.id
                }
            )
            support_agents.append(user)
            
        return sales_reps, support_agents

    def setup_products(self, tenant, admin_user):
        self.stdout.write('4. Setting up Products...')
        
        products = []
        p1, _ = Product.objects.get_or_create(
            sku='SAAS-ENT',
            tenant_id=tenant.id,
            defaults={
                'name': 'Enterprise License',
                'base_price': 5000.00,
                'pricing_model': 'subscription',
                'is_subscription': True,
                'billing_cycle': 'annually',
                'owner': admin_user
            }
        )
        products.append(p1)
        
        p2, _ = Product.objects.get_or_create(
            sku='SVC-IMPL',
            tenant_id=tenant.id,
            defaults={
                'name': 'Implementation Service',
                'base_price': 2500.00,
                'pricing_model': 'flat',
                'owner': admin_user
            }
        )
        products.append(p2)
        
        return products

    def setup_marketing(self, tenant, admin_user):
        self.stdout.write('5. Setting up Marketing...')
        
        campaign, _ = MarketingCampaign.objects.get_or_create(
            name="Q4 Outreach",
            tenant_id=tenant.id,
            defaults={
                'status': 'sending',
                'owner': admin_user,
                'send_date': timezone.now()
            }
        )
        
        template, _ = EmailTemplate.objects.get_or_create(
            name="Intro Email",
            tenant_id=tenant.id,
            defaults={
                'subject_line': "Transform your business with Acme",
                'html_content': "<p>Hi {{first_name}}, check out our new solution.</p>",
                'category': 'promotional'
            }
        )
        
        return campaign

    def simulate_sales_workflow(self, tenant, sales_reps, products, campaign):
        self.stdout.write('6. Simulating Sales Workflow...')
        
        # Ensure stages exist
        LeadStatus.objects.get_or_create(name='new', tenant_id=tenant.id, defaults={'label': 'New'})
        LeadStatus.objects.get_or_create(name='qualified', tenant_id=tenant.id, defaults={'label': 'Qualified', 'is_qualified': True})
        LeadStatus.objects.get_or_create(name='converted', tenant_id=tenant.id, defaults={'label': 'Converted', 'is_closed': True})
        
        OpportunityStage.objects.get_or_create(name='Discovery', tenant_id=tenant.id, defaults={'order': 1, 'probability': 10})
        OpportunityStage.objects.get_or_create(name='Proposal', tenant_id=tenant.id, defaults={'order': 2, 'probability': 50})
        won_stage, _ = OpportunityStage.objects.get_or_create(name='Closed Won', tenant_id=tenant.id, defaults={'order': 3, 'probability': 100, 'is_won': True})
        
        accounts = []
        opportunities = []
        
        # Create 10 Leads
        for i in range(10):
            rep = random.choice(sales_reps)
            lead = Lead.objects.create(
                first_name=f'Customer{i}',
                last_name='Doe',
                email=f'customer{i}@example.com',
                company=f'Company {i}',
                industry='tech',
                owner=rep,
                tenant_id=tenant.id,
                lead_source='web'
            )
            
            # Add to campaign
            CampaignRecipient.objects.create(
                campaign=campaign,
                email=lead.email,
                status='opened',
                opened_at=timezone.now(),
                tenant_id=tenant.id
            )
            
            # Progress 5 leads to Opportunities
            if i < 5:
                lead.status = 'converted'
                lead.save()
                
                account = Account.objects.create(
                    name=lead.company,
                    industry=lead.industry,
                    tier='silver',
                    country='US',
                    owner=rep,
                    tenant_id=tenant.id,
                    status='active'
                )
                accounts.append(account)
                
                contact = Contact.objects.create(
                    account=account,
                    first_name=lead.first_name,
                    last_name=lead.last_name,
                    email=lead.email,
                    tenant_id=tenant.id,
                    is_primary=True
                )
                
                opp = Opportunity.objects.create(
                    name=f"{account.name} Deal",
                    account=account,
                    amount=10000.00,
                    stage=OpportunityStage.objects.get(name='Discovery', tenant_id=tenant.id),
                    close_date=timezone.now() + timedelta(days=30),
                    owner=rep,
                    tenant_id=tenant.id
                )
                opportunities.append(opp)
                
                # Add products
                OpportunityProduct.objects.create(
                    opportunity=opp,
                    product=products[0],
                    quantity=1,
                    unit_price=products[0].base_price,
                    tenant_id=tenant.id
                )
                
                # Create Proposal
                proposal = Proposal.objects.create(
                    title=f"Proposal for {account.name}",
                    opportunity=opp,
                    status='sent',
                    content="<h1>Proposal</h1>",
                    sent_by=rep,
                    tenant_id=tenant.id
                )
                
                # Simulate Proposal View
                ProposalEvent.objects.create(
                    proposal=proposal,
                    event_type='viewed',
                    tenant_id=tenant.id
                )
                
                # Log Call
                Call.objects.create(
                    owner=rep,
                    account=account,
                    contact=contact,
                    outcome='connected',
                    duration=timedelta(minutes=15),
                    notes="Intro call went well",
                    tenant_id=tenant.id
                )
                
                # Close 3 deals
                if i < 3:
                    opp.stage = won_stage
                    opp.probability = 1.0
                    opp.save()
                    
                    WinLossAnalysis.objects.create(
                        opportunity=opp,
                        is_won=True,
                        win_reason="Good product fit",
                        tenant_id=tenant.id
                    )
        
        return accounts, opportunities

    def simulate_support_workflow(self, tenant, support_agents, accounts):
        self.stdout.write('7. Simulating Support Workflow...')
        
        if not accounts:
            return

        # Create 2 Cases
        for i in range(2):
            account = accounts[i]
            agent = random.choice(support_agents)
            
            case = Case.objects.create(
                subject=f"Issue with login {i}",
                description="Cannot access dashboard",
                account=account,
                contact=account.contacts.first(),
                priority='high',
                status='new',
                owner=agent,
                tenant_id=tenant.id
            )
            
            # Add comment
            CaseComment.objects.create(
                case=case,
                author=agent,
                content="Investigating now...",
                tenant_id=tenant.id
            )
            
            # Resolve 1 case
            if i == 0:
                case.status = 'resolved'
                case.resolved_at = timezone.now()
                case.save()
                
                # CSAT
                CsatResponse.objects.create(
                    case=case,
                    score=5,
                    comment="Great service!",
                    tenant_id=tenant.id
                )

    def setup_customer_success(self, tenant, admin_user, accounts):
        self.stdout.write('8. Setting up Customer Success...')
        
        # Knowledge Base
        cat, _ = Category.objects.get_or_create(name="General", tenant_id=tenant.id)
        article = Article.objects.create(
            title="Getting Started",
            slug="getting-started",
            category=cat,
            article_type='user_guide',
            status='published',
            author=admin_user,
            tenant_id=tenant.id
        )
        
        ArticleVersion.objects.create(
            article=article,
            content="Welcome to Acme...",
            version_number=1,
            is_current=True,
            created_by=admin_user,
            tenant_id=tenant.id
        )
        
        # NPS
        survey, _ = NpsSurvey.objects.get_or_create(
            name="Q4 NPS",
            tenant_id=tenant.id
        )
        
        if accounts:
            NpsResponse.objects.create(
                account=accounts[0],
                survey=survey,
                score=10,
                comment="Love the product",
                tenant_id=tenant.id
            )

    def simulate_commissions(self, tenant, admin_user, sales_reps, opportunities):
        self.stdout.write('9. Simulating Commissions...')
        
        # Create Plan
        plan, _ = CommissionPlan.objects.get_or_create(
            name="Standard Sales Plan",
            tenant_id=tenant.id,
            defaults={'basis': 'revenue', 'period': 'monthly'}
        )
        
        # Create Rule (10%)
        CommissionRule.objects.get_or_create(
            plan=plan,
            tenant_id=tenant.id,
            defaults={'rate_type': 'flat', 'rate_value': 10.00}
        )
        
        # Assign to Reps
        for rep in sales_reps:
            UserCommissionPlan.objects.get_or_create(
                user=rep,
                plan=plan,
                tenant_id=tenant.id,
                defaults={'start_date': timezone.now().date().replace(day=1)}
            )
            
        # Calculate Commissions for Won Deals
        won_opps = [o for o in opportunities if o.stage.is_won]
        for opp in won_opps:
            # Simple calculation logic (normally in a service)
            commission_amount = float(opp.amount) * 0.10
            Commission.objects.create(
                user=opp.owner,
                opportunity=opp,
                amount=commission_amount,
                rate_applied=10.00,
                date_earned=timezone.now().date(),
                status='approved',
                tenant_id=tenant.id
            )

    def simulate_reporting(self, tenant, admin_user):
        self.stdout.write('10. Verifying Reporting...')
        # Just a placeholder to indicate this step would involve checking views
        # In a real test we would call the view functions
        pass

    def print_summary(self, tenant):
        self.stdout.write('\n--- Simulation Summary ---')
        self.stdout.write(f'Tenant: {tenant.name}')
        self.stdout.write(f'Users: {User.objects.filter(tenant_id=tenant.id).count()}')
        self.stdout.write(f'Leads: {Lead.objects.filter(tenant_id=tenant.id).count()}')
        self.stdout.write(f'Opportunities: {Opportunity.objects.filter(tenant_id=tenant.id).count()}')
        self.stdout.write(f'Cases: {Case.objects.filter(tenant_id=tenant.id).count()}')
        self.stdout.write(f'Commissions: {Commission.objects.filter(tenant_id=tenant.id).count()}')
        self.stdout.write('--------------------------\n')
