"""
Integration tests for lead to opportunity conversion flow.

Tests verify the complete workflow of:
- Creating a lead
- Qualifying the lead
- Converting to an opportunity
- Tracking conversion metrics
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from leads.models import Lead
from opportunities.models import Opportunity
from accounts.models import Account
from tests.factories import (
    LeadFactory,
    LeadStatusFactory,
    AccountFactory,
    OpportunityFactory,
    OpportunityStageFactory,
    TenantFactory,
    UserFactory
)


@pytest.mark.django_db
@pytest.mark.integration
class TestLeadToOpportunityConversion:
    """Tests for lead to opportunity conversion flow."""
    
    def test_qualify_lead(self, lead, lead_status_qualified):
        """Test qualifying a lead updates status correctly."""
        # Start with new lead
        assert lead.status_ref.is_qualified is False
        
        # Qualify the lead
        lead.status_ref = lead_status_qualified
        lead.status = 'qualified'
        lead.lead_score = 75  # Increase score for qualified leads
        lead.save()
        
        lead.refresh_from_db()
        assert lead.status_ref.is_qualified is True
        assert lead.status == 'qualified'
        assert lead.lead_score >= 75
    
    def test_create_account_from_lead(self, lead, tenant, user):
        """Test creating an account from lead data."""
        # Create account using lead's company information
        account = AccountFactory.create(
            account_name=lead.company,
            industry=lead.industry,
            tenant=tenant,
            owner=user
        )
        
        assert account.account_name == lead.company
        assert account.industry == lead.industry
        assert account.tenant == tenant
    
    def test_create_opportunity_from_lead(self, lead, tenant, user, opportunity_stage_prospecting):
        """Test creating an opportunity from a qualified lead."""
        # First create an account from the lead
        account = AccountFactory.create(
            account_name=lead.company,
            tenant=tenant,
            owner=user
        )
        
        # Create opportunity based on lead
        opportunity = OpportunityFactory.create(
            opportunity_name=f"Opportunity - {lead.company}",
            account=account,
            stage=opportunity_stage_prospecting,
            amount=Decimal('50000.00'),
            tenant_id=tenant.tenant_id
        )
        
        assert opportunity.opportunity_name == f"Opportunity - {lead.company}"
        assert opportunity.account == account
        assert opportunity.tenant_id == tenant.tenant_id
    
    def test_full_conversion_flow(self, tenant, user, lead_statuses, opportunity_stages):
        """Test complete lead to opportunity conversion flow."""
        # Step 1: Create new lead
        lead = LeadFactory.create(
            first_name='John',
            last_name='Doe',
            company='Acme Corp',
            email='john@acme.com',
            owner=user,
            status_ref=lead_statuses['new'],
            tenant_id=tenant.tenant_id,
            lead_score=50
        )
        
        assert lead.status_ref.status_name == 'new'
        
        # Step 2: Qualify the lead
        lead.status_ref = lead_statuses['qualified']
        lead.status = 'qualified'
        lead.lead_score = 80
        lead.save()
        
        assert lead.status_ref.is_qualified is True
        
        # Step 3: Create account from lead
        account = AccountFactory.create(
            account_name=lead.company,
            tenant=tenant,
            owner=user
        )
        
        # Step 4: Create opportunity from qualified lead
        opportunity = OpportunityFactory.create(
            opportunity_name=f"Deal - {lead.company}",
            account=account,
            stage=opportunity_stages['prospecting'],
            amount=Decimal('75000.00'),
            tenant_id=tenant.tenant_id
        )
        
        # Step 5: Mark lead as converted (closed won)
        lead.status_ref = lead_statuses['closed_won']
        lead.status = 'closed_won'
        lead.save()
        
        # Verify final state
        lead.refresh_from_db()
        assert lead.status_ref.is_closed is True
        assert opportunity.account.account_name == lead.company
    
    def test_conversion_preserves_tenant(self, tenant, user, lead_statuses, opportunity_stages):
        """Test conversion flow maintains tenant isolation."""
        lead = LeadFactory.create(
            owner=user,
            status_ref=lead_statuses['new'],
            tenant_id=tenant.tenant_id
        )
        
        account = AccountFactory.create(
            account_name=lead.company,
            tenant=tenant,
            owner=user
        )
        
        opportunity = OpportunityFactory.create(
            account=account,
            stage=opportunity_stages['prospecting'],
            tenant_id=tenant.tenant_id
        )
        
        # All should have same tenant
        assert lead.tenant_id == tenant.tenant_id
        assert account.tenant == tenant
        assert opportunity.tenant_id == tenant.tenant_id


@pytest.mark.django_db
@pytest.mark.integration
class TestLeadConversionMetrics:
    """Tests for lead conversion tracking and metrics."""
    
    def test_count_qualified_leads(self, tenant, user, lead_statuses):
        """Test counting qualified leads."""
        # Create mix of lead statuses
        LeadFactory.create_batch(
            5,
            owner=user,
            status_ref=lead_statuses['new'],
            tenant_id=tenant.tenant_id
        )
        LeadFactory.create_batch(
            3,
            owner=user,
            status_ref=lead_statuses['qualified'],
            tenant_id=tenant.tenant_id
        )
        
        new_count = Lead.objects.filter(
            tenant_id=tenant.tenant_id,
            status_ref=lead_statuses['new']
        ).count()
        
        qualified_count = Lead.objects.filter(
            tenant_id=tenant.tenant_id,
            status_ref=lead_statuses['qualified']
        ).count()
        
        assert new_count == 5
        assert qualified_count == 3
    
    def test_count_closed_leads(self, tenant, user, lead_statuses):
        """Test counting closed leads (won and lost)."""
        LeadFactory.create_batch(
            2,
            owner=user,
            status_ref=lead_statuses['closed_won'],
            tenant_id=tenant.tenant_id
        )
        LeadFactory.create_batch(
            1,
            owner=user,
            status_ref=lead_statuses['closed_lost'],
            tenant_id=tenant.tenant_id
        )
        
        closed_won_count = Lead.objects.filter(
            tenant_id=tenant.tenant_id,
            status_ref__is_closed=True,
            status_ref__is_qualified=True
        ).count()
        
        closed_lost_count = Lead.objects.filter(
            tenant_id=tenant.tenant_id,
            status_ref__is_closed=True,
            status_ref__is_qualified=False
        ).count()
        
        assert closed_won_count == 2
        assert closed_lost_count == 1
    
    def test_conversion_rate_calculation(self, tenant, user, lead_statuses):
        """Test calculating lead conversion rate."""
        # Create leads
        LeadFactory.create_batch(
            7,
            owner=user,
            status_ref=lead_statuses['new'],
            tenant_id=tenant.tenant_id
        )
        LeadFactory.create_batch(
            3,
            owner=user,
            status_ref=lead_statuses['closed_won'],
            tenant_id=tenant.tenant_id
        )
        
        total_leads = Lead.objects.filter(tenant_id=tenant.tenant_id).count()
        converted_leads = Lead.objects.filter(
            tenant_id=tenant.tenant_id,
            status_ref=lead_statuses['closed_won']
        ).count()
        
        conversion_rate = (converted_leads / total_leads) * 100
        
        assert total_leads == 10
        assert converted_leads == 3
        assert conversion_rate == 30.0


@pytest.mark.django_db
@pytest.mark.integration
class TestOpportunityFromLeadValue:
    """Tests for calculating opportunity value from leads."""
    
    def test_opportunity_value_tracking(self, account, opportunity_stages):
        """Test tracking opportunity values."""
        opps = [
            OpportunityFactory.create(
                account=account,
                stage=opportunity_stages['prospecting'],
                amount=Decimal('25000.00'),
                tenant_id=account.tenant.tenant_id
            ),
            OpportunityFactory.create(
                account=account,
                stage=opportunity_stages['proposal'],
                amount=Decimal('50000.00'),
                tenant_id=account.tenant.tenant_id
            ),
            OpportunityFactory.create(
                account=account,
                stage=opportunity_stages['closed_won'],
                amount=Decimal('100000.00'),
                tenant_id=account.tenant.tenant_id
            ),
        ]
        
        total_pipeline = sum(opp.amount for opp in opps)
        won_value = sum(
            opp.amount for opp in opps 
            if opp.stage.is_won
        )
        
        assert total_pipeline == Decimal('175000.00')
        assert won_value == Decimal('100000.00')
