"""
Unit tests for Account and Contact models.

Tests cover:
- Model creation and validation
- Field constraints
- Model methods
- Manager methods
- String representations
"""
import pytest
from django.core.exceptions import ValidationError
from accounts.models import Account, Contact
from tests.factories import AccountFactory, ContactFactory, TenantFactory, UserFactory


@pytest.mark.django_db
class TestAccountModel:
    """Tests for the Account model."""
    
    def test_account_creation(self, account):
        """Test basic account creation."""
        assert account.pk is not None
        assert account.account_name is not None
        assert account.tenant is not None
    
    def test_account_str_representation(self, account):
        """Test account string representation."""
        assert str(account) == account.account_name
    
    def test_account_with_owner(self, account):
        """Test account has an owner."""
        assert account.owner is not None
        assert account.owner.tenant == account.tenant
    
    def test_account_enterprise_trait(self, enterprise_account):
        """Test enterprise account has high metrics."""
        assert enterprise_account.annual_revenue >= 50000000
        assert enterprise_account.employee_count >= 10000
    
    def test_account_tenant_relationship(self, tenant, user):
        """Test account is properly associated with tenant."""
        account = AccountFactory.create(tenant=tenant, owner=user)
        assert account.tenant == tenant
        assert account in tenant.accounts.all()
    
    def test_account_required_fields(self, tenant, user):
        """Test account requires account_name."""
        account = AccountFactory.build(
            tenant=tenant,
            owner=user,
            account_name=''
        )
        with pytest.raises(ValidationError):
            account.full_clean()
    
    def test_account_industry_choices(self, account):
        """Test account industry is from valid choices."""
        valid_industries = ['tech', 'finance', 'healthcare', 'retail', 'manufacturing', 'other']
        assert account.industry in valid_industries or account.industry is None


@pytest.mark.django_db
class TestContactModel:
    """Tests for the Contact model."""
    
    def test_contact_creation(self, account):
        """Test basic contact creation."""
        contact = ContactFactory.create(account=account, tenant=account.tenant)
        assert contact.pk is not None
        assert contact.first_name is not None
        assert contact.last_name is not None
    
    def test_contact_account_relationship(self, account):
        """Test contact is properly linked to account."""
        contact = ContactFactory.create(account=account, tenant=account.tenant)
        assert contact.account == account
        assert contact in account.contacts.all()
    
    def test_contact_email_format(self, account):
        """Test contact email is properly formatted."""
        contact = ContactFactory.create(account=account, tenant=account.tenant)
        assert '@' in contact.email
    
    def test_contact_str_representation(self, account):
        """Test contact string representation."""
        contact = ContactFactory.create(
            account=account,
            tenant=account.tenant,
            first_name='John',
            last_name='Doe'
        )
        assert 'John' in str(contact) or 'john' in str(contact).lower()
    
    def test_primary_contact_trait(self, account):
        """Test primary contact trait sets is_primary."""
        contact = ContactFactory.create(
            account=account,
            tenant=account.tenant,
            primary=True
        )
        assert contact.is_primary is True
    
    def test_decision_maker_trait(self, account):
        """Test decision maker trait sets correct attributes."""
        contact = ContactFactory.create(
            account=account,
            tenant=account.tenant,
            decision_maker=True
        )
        assert contact.is_decision_maker is True
        assert contact.job_title in ['CEO', 'CTO', 'CFO', 'VP of Sales', 'Director']


@pytest.mark.django_db
class TestAccountWithContacts:
    """Tests for Account and Contact relationships."""
    
    def test_account_with_multiple_contacts(self, account_with_contacts):
        """Test account has multiple contacts."""
        assert account_with_contacts.contacts.count() == 3
    
    def test_contacts_inherit_tenant(self, account_with_contacts):
        """Test all contacts belong to same tenant as account."""
        for contact in account_with_contacts.contacts.all():
            assert contact.tenant == account_with_contacts.tenant
    
    def test_delete_account_cascades_to_contacts(self, account_with_contacts):
        """Test deleting account deletes associated contacts."""
        account_id = account_with_contacts.pk
        contact_ids = list(account_with_contacts.contacts.values_list('pk', flat=True))
        
        account_with_contacts.delete()
        
        assert not Account.objects.filter(pk=account_id).exists()
        for contact_id in contact_ids:
            assert not Contact.objects.filter(pk=contact_id).exists()
