"""
SalesCompass Test Suite - Centralized pytest fixtures.

This conftest.py provides shared fixtures for all tests in the SalesCompass project.
Fixtures are organized by category:
    - Database and Django setup
    - Authentication fixtures
    - Model instance fixtures
    - Client fixtures
    - Utility fixtures
"""
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

# Import factories
from tests.factories import (
    UserFactory,
    SuperuserFactory,
    TenantFactory,
    AccountFactory,
    ContactFactory,
    LeadFactory,
    LeadStatusFactory,
    LeadSourceFactory,
    OpportunityFactory,
    OpportunityStageFactory,
)

User = get_user_model()


# =============================================================================
# Database and Django Setup Fixtures
# =============================================================================

@pytest.fixture
def db_access(db):
    """
    Marker fixture to explicitly request database access.
    
    Use this for tests that need database access but don't need
    any specific model instances.
    """
    pass


# =============================================================================
# Tenant Fixtures
# =============================================================================

@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    return TenantFactory.create()


@pytest.fixture
def tenant_trial(db):
    """Create a trial tenant."""
    return TenantFactory.create(trial=True)


@pytest.fixture
def tenant_suspended(db):
    """Create a suspended tenant."""
    return TenantFactory.create(suspended=True)


@pytest.fixture
def other_tenant(db):
    """Create a second tenant for isolation tests."""
    return TenantFactory.create(name="Other Tenant", subdomain="other")


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def user(db, tenant):
    """Create a regular test user belonging to the default tenant."""
    return UserFactory.create(tenant=tenant)


@pytest.fixture
def staff_user(db, tenant):
    """Create a staff user belonging to the default tenant."""
    return UserFactory.create(tenant=tenant, staff=True)


@pytest.fixture
def superuser(db):
    """Create a superuser (no tenant association)."""
    return SuperuserFactory.create()


@pytest.fixture
def other_user(db, other_tenant):
    """Create a user belonging to a different tenant for isolation tests."""
    return UserFactory.create(tenant=other_tenant)


# =============================================================================
# Client Fixtures
# =============================================================================

@pytest.fixture
def django_client():
    """Return a Django test client (not authenticated)."""
    return Client()


@pytest.fixture
def authenticated_client(django_client, user):
    """Return a Django test client authenticated as the regular user."""
    django_client.force_login(user)
    return django_client


@pytest.fixture
def staff_client(django_client, staff_user):
    """Return a Django test client authenticated as a staff user."""
    django_client.force_login(staff_user)
    return django_client


@pytest.fixture
def superuser_client(django_client, superuser):
    """Return a Django test client authenticated as a superuser."""
    django_client.force_login(superuser)
    return django_client


@pytest.fixture
def api_client():
    """Return a DRF API test client (not authenticated)."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """Return a DRF API test client authenticated as the regular user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def superuser_api_client(api_client, superuser):
    """Return a DRF API test client authenticated as a superuser."""
    api_client.force_authenticate(user=superuser)
    return api_client


# =============================================================================
# Account Fixtures
# =============================================================================

@pytest.fixture
def account(db, tenant, user):
    """Create a test account."""
    return AccountFactory.create(tenant=tenant, owner=user)


@pytest.fixture
def enterprise_account(db, tenant, user):
    """Create an enterprise-tier account."""
    return AccountFactory.create(tenant=tenant, owner=user, enterprise=True)


@pytest.fixture
def account_with_contacts(db, tenant, user):
    """Create an account with multiple contacts."""
    account = AccountFactory.create(tenant=tenant, owner=user)
    ContactFactory.create_batch(3, account=account, tenant=tenant)
    return account


# =============================================================================
# Lead Fixtures
# =============================================================================

@pytest.fixture
def lead_status_new(db, tenant):
    """Create a 'New' lead status."""
    return LeadStatusFactory.create(
        status_name='new',
        label='New',
        order=1,
        tenant_id=tenant.tenant_id
    )


@pytest.fixture
def lead_status_qualified(db, tenant):
    """Create a 'Qualified' lead status."""
    return LeadStatusFactory.create(
        status_name='qualified',
        label='Qualified',
        order=2,
        is_qualified=True,
        tenant_id=tenant.tenant_id
    )


@pytest.fixture
def lead_statuses(db, tenant, lead_status_new, lead_status_qualified):
    """Create a full set of lead statuses for pipeline testing."""
    closed_won = LeadStatusFactory.create(
        status_name='closed_won',
        label='Closed Won',
        order=3,
        is_closed=True,
        is_qualified=True,
        tenant_id=tenant.tenant_id
    )
    closed_lost = LeadStatusFactory.create(
        status_name='closed_lost',
        label='Closed Lost',
        order=4,
        is_closed=True,
        tenant_id=tenant.tenant_id
    )
    return {
        'new': lead_status_new,
        'qualified': lead_status_qualified,
        'closed_won': closed_won,
        'closed_lost': closed_lost,
    }


@pytest.fixture
def lead(db, user, lead_status_new):
    """Create a test lead."""
    return LeadFactory.create(
        owner=user,
        status_ref=lead_status_new,
        tenant_id=user.tenant.tenant_id
    )


@pytest.fixture
def high_value_lead(db, user, lead_status_new):
    """Create a high-value lead."""
    return LeadFactory.create(
        owner=user,
        status_ref=lead_status_new,
        tenant_id=user.tenant.tenant_id,
        high_value=True
    )


@pytest.fixture
def leads_batch(db, user, lead_status_new):
    """Create a batch of 10 leads."""
    return LeadFactory.create_batch(
        10,
        owner=user,
        status_ref=lead_status_new,
        tenant_id=user.tenant.tenant_id
    )


# =============================================================================
# Opportunity Fixtures
# =============================================================================

@pytest.fixture
def opportunity_stage_prospecting(db, tenant):
    """Create a 'Prospecting' opportunity stage."""
    return OpportunityStageFactory.create(
        prospecting=True,
        tenant_id=tenant.tenant_id
    )


@pytest.fixture
def opportunity_stage_closed_won(db, tenant):
    """Create a 'Closed Won' opportunity stage."""
    return OpportunityStageFactory.create(
        closed_won=True,
        tenant_id=tenant.tenant_id
    )


@pytest.fixture
def opportunity_stages(db, tenant, opportunity_stage_prospecting):
    """Create a full set of opportunity stages for pipeline testing."""
    qualification = OpportunityStageFactory.create(
        qualification=True,
        tenant_id=tenant.tenant_id
    )
    proposal = OpportunityStageFactory.create(
        proposal=True,
        tenant_id=tenant.tenant_id
    )
    negotiation = OpportunityStageFactory.create(
        negotiation=True,
        tenant_id=tenant.tenant_id
    )
    closed_won = OpportunityStageFactory.create(
        closed_won=True,
        tenant_id=tenant.tenant_id
    )
    closed_lost = OpportunityStageFactory.create(
        closed_lost=True,
        tenant_id=tenant.tenant_id
    )
    return {
        'prospecting': opportunity_stage_prospecting,
        'qualification': qualification,
        'proposal': proposal,
        'negotiation': negotiation,
        'closed_won': closed_won,
        'closed_lost': closed_lost,
    }


@pytest.fixture
def opportunity(db, account, opportunity_stage_prospecting):
    """Create a test opportunity."""
    return OpportunityFactory.create(
        account=account,
        stage=opportunity_stage_prospecting,
        tenant_id=account.tenant.tenant_id
    )


@pytest.fixture
def won_opportunity(db, account, opportunity_stage_closed_won):
    """Create a won opportunity."""
    return OpportunityFactory.create(
        account=account,
        stage=opportunity_stage_closed_won,
        won=True,
        tenant_id=account.tenant.tenant_id
    )


@pytest.fixture
def opportunities_batch(db, account, opportunity_stage_prospecting):
    """Create a batch of 10 opportunities."""
    return OpportunityFactory.create_batch(
        10,
        account=account,
        stage=opportunity_stage_prospecting,
        tenant_id=account.tenant.tenant_id
    )


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def mock_request(rf, user):
    """
    Create a mock request object with an authenticated user.
    
    Useful for testing views that require request.user.
    """
    request = rf.get('/')
    request.user = user
    return request


@pytest.fixture
def tenant_context(tenant, user):
    """
    Return a dict with common tenant context data.
    
    Useful for creating objects that need tenant_id.
    """
    return {
        'tenant': tenant,
        'tenant_id': tenant.tenant_id,
        'user': user,
    }
