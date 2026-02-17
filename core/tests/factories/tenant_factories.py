"""
Tenant model factories for testing.

Provides factories for:
- Tenant (multi-tenant isolation)
"""
import factory
from factory.django import DjangoModelFactory
from tenants.models import Tenant


class TenantFactory(DjangoModelFactory):
    """Factory for creating Tenant instances."""
    
    class Meta:
        model = Tenant
        skip_postgeneration_save = True
    
    name = factory.Sequence(lambda n: f'Test Tenant {n}')
    tenant_id = factory.Sequence(lambda n: f'tenant_{n}')
    subdomain = factory.Sequence(lambda n: f'tenant{n}')
    is_active = True
    status = 'active'
    
    # Plan relationship (optional, can be set via fixture)
    plan = None
    
    class Params:
        # Trait for suspended tenants
        suspended = factory.Trait(
            is_active=False,
            status='suspended'
        )
        
        # Trait for trial tenants
        trial = factory.Trait(
            status='trial'
        )
        
        # Trait for archived tenants
        archived = factory.Trait(
            is_active=False,
            status='archived'
        )


class TenantWithAdminFactory(TenantFactory):
    """Factory for creating Tenant with an admin user."""
    
    @factory.post_generation
    def admin(self, create, extracted, **kwargs):
        """Create and assign a tenant admin after tenant creation."""
        if not create:
            return
        
        from tests.factories.core_factories import UserFactory
        
        if extracted:
            self.tenant_admin = extracted
        else:
            admin_user = UserFactory.create(tenant=self, is_staff=True)
            self.tenant_admin = admin_user
        
        self.save()
