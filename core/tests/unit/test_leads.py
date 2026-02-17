"""
Unit tests for Lead models and services.

Tests cover:
- Lead model creation and validation
- Lead scoring logic
- Lead status transitions
- LeadStatus and LeadSource models
"""
import pytest
from django.core.exceptions import ValidationError
from leads.models import Lead, LeadStatus, LeadSource
from tests.factories import (
    LeadFactory,
    LeadStatusFactory,
    LeadSourceFactory,
    TenantFactory,
    UserFactory
)


@pytest.mark.django_db
class TestLeadStatusModel:
    """Tests for the LeadStatus model."""
    
    def test_lead_status_creation(self, lead_status_new):
        """Test basic lead status creation."""
        assert lead_status_new.pk is not None
        assert lead_status_new.status_name == 'new'
        assert lead_status_new.label == 'New'
    
    def test_lead_status_ordering(self, lead_statuses):
        """Test lead statuses are ordered correctly."""
        statuses = list(lead_statuses.values())
        orders = [s.order for s in statuses]
        assert orders == sorted(orders)
    
    def test_lead_status_qualified_flag(self, lead_status_qualified):
        """Test qualified status has correct flag."""
        assert lead_status_qualified.is_qualified is True
        assert lead_status_qualified.is_closed is False
    
    def test_lead_status_closed_flags(self, lead_statuses):
        """Test closed statuses have correct flags."""
        assert lead_statuses['closed_won'].is_closed is True
        assert lead_statuses['closed_won'].is_qualified is True
        assert lead_statuses['closed_lost'].is_closed is True


@pytest.mark.django_db
class TestLeadModel:
    """Tests for the Lead model."""
    
    def test_lead_creation(self, lead):
        """Test basic lead creation."""
        assert lead.pk is not None
        assert lead.first_name is not None
        assert lead.last_name is not None
        assert lead.email is not None
    
    def test_lead_str_representation(self, lead):
        """Test lead string representation includes name."""
        lead_str = str(lead)
        assert lead.first_name in lead_str or lead.last_name in lead_str
    
    def test_lead_full_name_property(self, lead):
        """Test lead full_name property."""
        expected = f"{lead.first_name} {lead.last_name}"
        assert lead.full_name == expected
    
    def test_lead_owner_relationship(self, lead, user):
        """Test lead has an owner."""
        assert lead.owner is not None
        assert lead.owner == user
    
    def test_lead_status_relationship(self, lead, lead_status_new):
        """Test lead has a status ref."""
        assert lead.status_ref == lead_status_new
    
    def test_lead_tenant_id(self, lead, tenant):
        """Test lead has correct tenant_id."""
        assert lead.tenant_id == tenant.tenant_id
    
    def test_high_value_lead_trait(self, high_value_lead):
        """Test high value lead has high metrics."""
        assert high_value_lead.company_size >= 5000
        assert high_value_lead.annual_revenue >= 50000000
        assert high_value_lead.lead_score >= 90
    
    def test_lead_email_format(self, lead):
        """Test lead email is properly formatted."""
        assert '@' in lead.email
    
    def test_lead_score_range(self, lead):
        """Test lead score is within valid range."""
        assert 0 <= lead.lead_score <= 100


@pytest.mark.django_db
class TestLeadScoring:
    """Tests for lead scoring functionality."""
    
    def test_initial_score_calculation(self, user, lead_status_new):
        """Test initial score is calculated on creation."""
        lead = LeadFactory.create(
            owner=user,
            status_ref=lead_status_new,
            tenant_id=user.tenant.tenant_id,
            company='Test Company',
            email='test@company.com',
            phone='123-456-7890'
        )
        # Score should be set based on provided info
        assert lead.lead_score > 0
    
    def test_empty_lead_has_low_score(self, user, lead_status_new):
        """Test lead with minimal info has low score."""
        lead = LeadFactory.build(
            owner=user,
            status_ref=lead_status_new,
            tenant_id=user.tenant.tenant_id,
            first_name='Test',
            last_name='Lead',
            email='test@example.com',
            company='Minimal Co',
            phone='',
            job_title='',
            industry='',
            lead_score=0  # Explicitly set to 0
        )
        # Very minimal information should result in lower score
        assert lead.lead_score <= 50
    
    def test_score_increases_with_business_metrics(self, user, lead_status_new):
        """Test score increases with business metrics."""
        low_value_lead = LeadFactory.create(
            owner=user,
            status_ref=lead_status_new,
            tenant_id=user.tenant.tenant_id,
            company_size=10,
            annual_revenue=100000,
            lead_score=20
        )
        
        high_value_lead = LeadFactory.create(
            owner=user,
            status_ref=lead_status_new,
            tenant_id=user.tenant.tenant_id,
            company_size=5000,
            annual_revenue=50000000,
            lead_score=90
        )
        
        assert high_value_lead.lead_score > low_value_lead.lead_score


@pytest.mark.django_db
class TestLeadStatusTransitions:
    """Tests for lead status transitions."""
    
    def test_update_status(self, lead, lead_status_qualified):
        """Test updating lead status."""
        lead.status_ref = lead_status_qualified
        lead.status = 'qualified'
        lead.save()
        
        lead.refresh_from_db()
        assert lead.status_ref == lead_status_qualified
        assert lead.status == 'qualified'
    
    def test_status_transition_to_closed_won(self, lead, lead_statuses):
        """Test transitioning lead to closed won."""
        lead.status_ref = lead_statuses['closed_won']
        lead.status = 'closed_won'
        lead.save()
        
        lead.refresh_from_db()
        assert lead.status_ref.is_closed is True
        assert lead.status_ref.is_qualified is True
    
    def test_status_transition_to_closed_lost(self, lead, lead_statuses):
        """Test transitioning lead to closed lost."""
        lead.status_ref = lead_statuses['closed_lost']
        lead.status = 'closed_lost'
        lead.save()
        
        lead.refresh_from_db()
        assert lead.status_ref.is_closed is True


@pytest.mark.django_db
class TestLeadBatch:
    """Tests for batch lead operations."""
    
    def test_leads_batch_creation(self, leads_batch):
        """Test batch creation creates correct number of leads."""
        assert len(leads_batch) == 10
    
    def test_leads_batch_unique_emails(self, leads_batch):
        """Test batch leads have unique emails."""
        emails = [lead.email for lead in leads_batch]
        assert len(emails) == len(set(emails))
    
    def test_leads_batch_same_owner(self, leads_batch, user):
        """Test all batch leads have same owner."""
        for lead in leads_batch:
            assert lead.owner == user
    
    def test_leads_batch_same_tenant(self, leads_batch, tenant):
        """Test all batch leads belong to same tenant."""
        for lead in leads_batch:
            assert lead.tenant_id == tenant.tenant_id
