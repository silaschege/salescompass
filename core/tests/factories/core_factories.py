"""
Core model factories for testing.

Provides factories for:
- User (regular users)
- Superuser (admin users)
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating regular User instances."""
    
    class Meta:
        model = User
        skip_postgeneration_save = True
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    # Tenant relationship
    tenant = factory.SubFactory('tests.factories.tenant_factories.TenantFactory')
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set the password after user creation."""
        password = extracted or 'testpass123'
        self.set_password(password)
        if create:
            self.save()
    
    class Params:
        # Trait for inactive users
        inactive = factory.Trait(is_active=False)
        
        # Trait for staff users
        staff = factory.Trait(is_staff=True)


class SuperuserFactory(UserFactory):
    """Factory for creating superuser instances."""
    
    is_staff = True
    is_superuser = True
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    username = factory.Sequence(lambda n: f'admin{n}')
    
    # Superusers may not belong to a tenant
    tenant = None
