"""
Leads app model factories for testing.

Provides factories for:
- Lead (potential customers)
- LeadStatus (workflow stages)
- LeadSource (acquisition channels)
"""
import factory
from factory.django import DjangoModelFactory
from leads.models import Lead, LeadStatus, LeadSource


class LeadStatusFactory(DjangoModelFactory):
    """Factory for creating LeadStatus instances."""
    
    class Meta:
        model = LeadStatus
        skip_postgeneration_save = True
        django_get_or_create = ('status_name', 'tenant_id')
    
    status_name = factory.Sequence(lambda n: f'status_{n}')
    label = factory.LazyAttribute(lambda obj: obj.status_name.replace('_', ' ').title())
    order = factory.Sequence(lambda n: n)
    is_active = True
    is_qualified = False
    is_closed = False
    
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.tenant_id if hasattr(obj, 'tenant') and obj.tenant else 'default_tenant')
    
    class Params:
        # Trait for qualified status
        qualified = factory.Trait(
            status_name='qualified',
            label='Qualified',
            is_qualified=True
        )
        
        # Trait for closed won status
        closed_won = factory.Trait(
            status_name='closed_won',
            label='Closed Won',
            is_closed=True,
            is_qualified=True
        )
        
        # Trait for closed lost status
        closed_lost = factory.Trait(
            status_name='closed_lost',
            label='Closed Lost',
            is_closed=True
        )


class LeadSourceFactory(DjangoModelFactory):
    """Factory for creating LeadSource instances."""
    
    class Meta:
        model = LeadSource
        skip_postgeneration_save = True
        django_get_or_create = ('source_name', 'tenant_id')
    
    source_name = factory.Sequence(lambda n: f'source_{n}')
    label = factory.LazyAttribute(lambda obj: obj.source_name.replace('_', ' ').title())
    order = factory.Sequence(lambda n: n)
    is_active = True
    
    tenant_id = factory.LazyAttribute(lambda obj: obj.tenant.tenant_id if hasattr(obj, 'tenant') and obj.tenant else 'default_tenant')


class LeadFactory(DjangoModelFactory):
    """Factory for creating Lead instances."""
    
    class Meta:
        model = Lead
        skip_postgeneration_save = True
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@example.com')
    phone = factory.Faker('phone_number')
    company = factory.Faker('company')
    job_title = factory.Faker('job')
    industry = factory.Faker('random_element', elements=['tech', 'finance', 'healthcare', 'retail', 'manufacturing'])
    
    # Business metrics
    company_size = factory.Faker('random_int', min=10, max=5000)
    annual_revenue = factory.Faker('random_int', min=100000, max=10000000)
    
    # Lead scoring
    lead_score = factory.Faker('random_int', min=0, max=100)
    
    # Status
    status = 'new'
    status_ref = factory.SubFactory(LeadStatusFactory)
    
    # Source
    source = 'web'
    source_ref = factory.SubFactory(LeadSourceFactory)
    
    # Owner relationship
    owner = factory.SubFactory('tests.factories.core_factories.UserFactory')
    
    # Tenant relationship
    tenant_id = factory.LazyAttribute(lambda obj: obj.owner.tenant.tenant_id if obj.owner and obj.owner.tenant else 'default_tenant')
    
    class Params:
        # Trait for high-value leads
        high_value = factory.Trait(
            company_size=5000,
            annual_revenue=50000000,
            lead_score=90
        )
        
        # Trait for qualified leads
        qualified = factory.Trait(
            lead_score=75,
            status='qualified'
        )
        
        # Trait for cold leads
        cold = factory.Trait(
            lead_score=10,
            status='cold'
        )
