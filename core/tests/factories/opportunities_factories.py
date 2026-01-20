"""
Opportunities app model factories for testing.

Provides factories for:
- Opportunity (sales deals)
- OpportunityStage (pipeline stages)
"""
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from opportunities.models import Opportunity, OpportunityStage


class OpportunityStageFactory(DjangoModelFactory):
    """Factory for creating OpportunityStage instances."""
    
    class Meta:
        model = OpportunityStage
        skip_postgeneration_save = True
        django_get_or_create = ('name', 'tenant_id')
    
    name = factory.Sequence(lambda n: f'stage_{n}')
    label = factory.LazyAttribute(lambda obj: obj.name.replace('_', ' ').title())
    order = factory.Sequence(lambda n: n)
    probability = Decimal('25.00')
    is_won = False
    is_lost = False
    
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.tenant_id if hasattr(obj, 'tenant') and obj.tenant else 'default_tenant')
    
    class Params:
        # Trait for prospecting stage
        prospecting = factory.Trait(
            name='prospecting',
            label='Prospecting',
            order=1,
            probability=Decimal('10.00')
        )
        
        # Trait for qualification stage
        qualification = factory.Trait(
            name='qualification',
            label='Qualification',
            order=2,
            probability=Decimal('25.00')
        )
        
        # Trait for proposal stage
        proposal = factory.Trait(
            name='proposal',
            label='Proposal',
            order=3,
            probability=Decimal('50.00')
        )
        
        # Trait for negotiation stage
        negotiation = factory.Trait(
            name='negotiation',
            label='Negotiation',
            order=4,
            probability=Decimal('75.00')
        )
        
        # Trait for closed won stage
        closed_won = factory.Trait(
            name='closed_won',
            label='Closed Won',
            order=5,
            probability=Decimal('100.00'),
            is_won=True
        )
        
        # Trait for closed lost stage
        closed_lost = factory.Trait(
            name='closed_lost',
            label='Closed Lost',
            order=6,
            probability=Decimal('0.00'),
            is_lost=True
        )


class OpportunityFactory(DjangoModelFactory):
    """Factory for creating Opportunity instances."""
    
    class Meta:
        model = Opportunity
        skip_postgeneration_save = True
    
    opportunity_name = factory.Sequence(lambda n: f'Opportunity {n}')
    amount = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True, min_value=1000, max_value=1000000)
    
    # Dates
    expected_closing_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=30))
    
    # Stage relationship
    stage = factory.SubFactory(OpportunityStageFactory)
    
    # Account relationship
    account = factory.SubFactory('tests.factories.accounts_factories.AccountFactory')
    
    # Owner relationship
    owner = factory.LazyAttribute(lambda obj: obj.account.owner if obj.account else None)
    
    # Tenant relationship
    tenant_id = factory.LazyAttribute(lambda obj: obj.account.tenant.tenant_id if obj.account and obj.account.tenant else 'default_tenant')
    
    # Probability (from stage)
    probability = factory.LazyAttribute(lambda obj: obj.stage.probability if obj.stage else Decimal('25.00'))
    
    class Params:
        # Trait for large deals
        large_deal = factory.Trait(
            amount=Decimal('500000.00'),
            deal_size_category='enterprise'
        )
        
        # Trait for small deals
        small_deal = factory.Trait(
            amount=Decimal('10000.00'),
            deal_size_category='small'
        )
        
        # Trait for urgent deals (closing soon)
        urgent = factory.Trait(
            expected_closing_date=factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=7))
        )
        
        # Trait for won deals
        won = factory.Trait(
            stage=factory.SubFactory(OpportunityStageFactory, closed_won=True),
            probability=Decimal('100.00'),
            closed_date=factory.LazyFunction(lambda: timezone.now().date())
        )
        
        # Trait for lost deals
        lost = factory.Trait(
            stage=factory.SubFactory(OpportunityStageFactory, closed_lost=True),
            probability=Decimal('0.00'),
            closed_date=factory.LazyFunction(lambda: timezone.now().date())
        )
