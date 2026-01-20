"""
Accounts app model factories for testing.

Provides factories for:
- Account (companies/organizations)
- Contact (people at accounts)
"""
import factory
from factory.django import DjangoModelFactory
from accounts.models import Account, Contact


class AccountFactory(DjangoModelFactory):
    """Factory for creating Account instances."""
    
    class Meta:
        model = Account
        skip_postgeneration_save = True
    
    account_name = factory.Sequence(lambda n: f'Acme Corp {n}')
    industry = factory.Faker('random_element', elements=['tech', 'finance', 'healthcare', 'retail', 'manufacturing'])
    website = factory.Faker('url')
    phone = factory.Faker('phone_number')
    email = factory.Faker('company_email')
    
    # Address fields
    address_line_1 = factory.Faker('street_address')
    city = factory.Faker('city')
    state = factory.Faker('state_abbr')
    country = factory.Faker('country_code')
    postal_code = factory.Faker('postcode')
    
    # Business metrics
    annual_revenue = factory.Faker('random_int', min=100000, max=10000000)
    employee_count = factory.Faker('random_int', min=10, max=5000)
    
    # Tenant relationship
    tenant = factory.SubFactory('tests.factories.tenant_factories.TenantFactory')
    
    # Owner relationship
    owner = factory.SubFactory('tests.factories.core_factories.UserFactory', tenant=factory.SelfAttribute('..tenant'))
    
    class Params:
        # Trait for enterprise accounts
        enterprise = factory.Trait(
            annual_revenue=50000000,
            employee_count=10000,
            tier='enterprise'
        )
        
        # Trait for SMB accounts
        smb = factory.Trait(
            annual_revenue=1000000,
            employee_count=50,
            tier='smb'
        )


class ContactFactory(DjangoModelFactory):
    """Factory for creating Contact instances."""
    
    class Meta:
        model = Contact
        skip_postgeneration_save = True
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@example.com')
    phone = factory.Faker('phone_number')
    job_title = factory.Faker('job')
    department = factory.Faker('random_element', elements=['Sales', 'Marketing', 'Engineering', 'Finance', 'Operations'])
    
    # Account relationship
    account = factory.SubFactory(AccountFactory)
    
    # Tenant relationship (should match account's tenant)
    tenant = factory.LazyAttribute(lambda obj: obj.account.tenant if obj.account else None)
    
    class Params:
        # Trait for primary contact
        primary = factory.Trait(
            is_primary=True
        )
        
        # Trait for decision maker
        decision_maker = factory.Trait(
            is_decision_maker=True,
            job_title=factory.Faker('random_element', elements=['CEO', 'CTO', 'CFO', 'VP of Sales', 'Director'])
        )
