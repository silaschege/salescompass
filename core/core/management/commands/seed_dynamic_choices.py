from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from core.models import User
from tenants.models import Tenant

class Command(BaseCommand):
    help = 'Seed dynamic choice models from hardcoded choices in models'

    def handle(self, *args, **options):
        tenants = Tenant.objects.all()
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('No tenants found.'))
            return

        # Core System Config
        system_config_types = [
            ('string', 'String'),
            ('integer', 'Integer'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
            ('file', 'File Path'),
        ]
        system_config_categories = [
            ('general', 'General'),
            ('security', 'Security'),
            ('email', 'Email'),
            ('authentication', 'Authentication'),
            ('integration', 'Integration'),
            ('performance', 'Performance'),
        ]

        # Leads choices
        lead_sources = [
            ('web_form', 'Web Form'),
            ('manual', 'Manual Entry'),
            ('referral', 'Referral'),
            ('api', 'External API'),
            ('partner', 'Partner'),
            ('event', 'Event/Trade Show'),
        ]
        lead_statuses = [
            ('new', 'New'),
            ('contacted', 'Contacted'),
            ('qualified', 'Qualified'),
            ('unqualified', 'Unqualified'),
            ('converted', 'Converted'),
        ]
        industries = [
            ('technology', 'Technology'),
            ('finance', 'Finance'),
            ('healthcare', 'Healthcare'),
            ('education', 'Education'),
            ('manufacturing', 'Manufacturing'),
            ('other', 'Other'),
        ]
        marketing_channels = [
            ('organic', 'Organic Search'),
            ('paid', 'Paid Search'),
            ('social', 'Social Media'),
            ('email', 'Email Marketing'),
            ('direct', 'Direct Traffic'),
        ]

        with transaction.atomic():
            # 1. System-wide choices (no tenant linked in some models, let's check core/models.py)
            # SystemConfigType and SystemConfigCategory do NOT have tenant link in core/models.py
            from core.models import SystemConfigType, SystemConfigCategory
            
            for name, display in system_config_types:
                SystemConfigType.objects.get_or_create(name=name, defaults={'display_name': display})
            
            for name, display in system_config_categories:
                SystemConfigCategory.objects.get_or_create(name=name, defaults={'display_name': display})

            # 2. Tenant-specific choices
            for tenant in tenants:
                self.stdout.write(f"Seeding choices for tenant: {tenant.name}")
                
                # Leads
                from leads.models import LeadSource, LeadStatus, Industry, MarketingChannel
                for name, display in lead_sources:
                    LeadSource.objects.get_or_create(tenant=tenant, source_name=name, defaults={'label': display})
                
                for name, display in lead_statuses:
                    LeadStatus.objects.get_or_create(tenant=tenant, status_name=name, defaults={'label': display})
                
                for name, display in industries:
                    Industry.objects.get_or_create(tenant=tenant, industry_name=name, defaults={'label': display})
                
                for name, display in marketing_channels:
                    MarketingChannel.objects.get_or_create(tenant=tenant, channel_name=name, defaults={'label': display})
                
                # Opportunities
                from opportunities.models import OpportunityStage, PipelineType, DealSizeCategory
                pipeline, _ = PipelineType.objects.get_or_create(tenant=tenant, pipeline_type_name='sales', defaults={'label': 'Sales Pipeline'})
                
                stages = [
                    ('prospecting', 'Prospecting', 10),
                    ('qualification', 'Qualification', 20),
                    ('proposal', 'Proposal', 50),
                    ('negotiation', 'Negotiation', 80),
                    ('closed_won', 'Closed Won', 100),
                    ('closed_lost', 'Closed Lost', 0),
                ]
                for name, label, prob in stages:
                    OpportunityStage.objects.get_or_create(
                        tenant=tenant, 
                        opportunity_stage_name=label, 
                        defaults={
                            'order': stages.index((name, label, prob)),
                            'probability': prob,
                            'is_won': name == 'closed_won',
                            'is_lost': name == 'closed_lost'
                        }
                    )
                
                deal_sizes = [
                    ('small', 'Small'),
                    ('medium', 'Medium'),
                    ('large', 'Large'),
                    ('enterprise', 'Enterprise'),
                ]
                for name, label in deal_sizes:
                    DealSizeCategory.objects.get_or_create(tenant=tenant, category_name=name, defaults={'label': label})

        self.stdout.write(self.style.SUCCESS("Successfully seeded dynamic choices."))
