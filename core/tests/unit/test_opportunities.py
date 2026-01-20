"""
Unit tests for Opportunity models.

Tests cover:
- Opportunity model creation and validation
- OpportunityStage model
- Stage transitions
- Pipeline calculations
- Weighted value calculations
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from opportunities.models import Opportunity, OpportunityStage
from tests.factories import (
    OpportunityFactory,
    OpportunityStageFactory,
    AccountFactory,
    TenantFactory,
    UserFactory
)


@pytest.mark.django_db
class TestOpportunityStageModel:
    """Tests for the OpportunityStage model."""
    
    def test_stage_creation(self, opportunity_stage_prospecting):
        """Test basic stage creation."""
        assert opportunity_stage_prospecting.pk is not None
        assert opportunity_stage_prospecting.name == 'prospecting'
        assert opportunity_stage_prospecting.label == 'Prospecting'
    
    def test_stage_probability(self, opportunity_stages):
        """Test stages have correct probabilities."""
        assert opportunity_stages['prospecting'].probability == Decimal('10.00')
        assert opportunity_stages['qualification'].probability == Decimal('25.00')
        assert opportunity_stages['proposal'].probability == Decimal('50.00')
        assert opportunity_stages['negotiation'].probability == Decimal('75.00')
        assert opportunity_stages['closed_won'].probability == Decimal('100.00')
        assert opportunity_stages['closed_lost'].probability == Decimal('0.00')
    
    def test_stage_ordering(self, opportunity_stages):
        """Test stages are ordered correctly."""
        orders = [
            opportunity_stages['prospecting'].order,
            opportunity_stages['qualification'].order,
            opportunity_stages['proposal'].order,
        ]
        assert orders == sorted(orders)
    
    def test_closed_won_flags(self, opportunity_stages):
        """Test closed won stage has correct flags."""
        assert opportunity_stages['closed_won'].is_won is True
        assert opportunity_stages['closed_won'].is_lost is False
    
    def test_closed_lost_flags(self, opportunity_stages):
        """Test closed lost stage has correct flags."""
        assert opportunity_stages['closed_lost'].is_won is False
        assert opportunity_stages['closed_lost'].is_lost is True


@pytest.mark.django_db
class TestOpportunityModel:
    """Tests for the Opportunity model."""
    
    def test_opportunity_creation(self, opportunity):
        """Test basic opportunity creation."""
        assert opportunity.pk is not None
        assert opportunity.opportunity_name is not None
        assert opportunity.amount is not None
        assert opportunity.amount > 0
    
    def test_opportunity_str_representation(self, opportunity):
        """Test opportunity string representation."""
        opp_str = str(opportunity)
        assert opportunity.opportunity_name in opp_str
    
    def test_opportunity_account_relationship(self, opportunity, account):
        """Test opportunity is linked to account."""
        assert opportunity.account == account
        assert opportunity in account.opportunities.all()
    
    def test_opportunity_stage_relationship(self, opportunity, opportunity_stage_prospecting):
        """Test opportunity has a stage."""
        assert opportunity.stage == opportunity_stage_prospecting
    
    def test_opportunity_expected_closing_date(self, opportunity):
        """Test opportunity has expected closing date set."""
        assert opportunity.expected_closing_date is not None
        assert opportunity.expected_closing_date >= timezone.now().date()
    
    def test_opportunity_tenant_id(self, opportunity, tenant):
        """Test opportunity has correct tenant_id."""
        assert opportunity.tenant_id == tenant.tenant_id


@pytest.mark.django_db
class TestOpportunityCalculations:
    """Tests for opportunity value calculations."""
    
    def test_weighted_value(self, account, opportunity_stages):
        """Test weighted value calculation."""
        opp = OpportunityFactory.create(
            account=account,
            stage=opportunity_stages['proposal'],
            amount=Decimal('100000.00'),
            probability=Decimal('50.00'),
            tenant_id=account.tenant.tenant_id
        )
        
        expected = Decimal('100000.00') * Decimal('0.50')
        assert opp.weighted_value == expected
    
    def test_weighted_value_prospecting(self, account, opportunity_stages):
        """Test weighted value at prospecting stage."""
        opp = OpportunityFactory.create(
            account=account,
            stage=opportunity_stages['prospecting'],
            amount=Decimal('100000.00'),
            probability=Decimal('10.00'),
            tenant_id=account.tenant.tenant_id
        )
        
        expected = Decimal('100000.00') * Decimal('0.10')
        assert opp.weighted_value == expected
    
    def test_weighted_value_closed_won(self, won_opportunity):
        """Test weighted value for won opportunity is full amount."""
        expected = won_opportunity.amount * Decimal('1.00')
        assert won_opportunity.weighted_value == expected


@pytest.mark.django_db
class TestOpportunityStageTransitions:
    """Tests for opportunity stage transitions."""
    
    def test_move_to_qualification(self, opportunity, opportunity_stages):
        """Test moving opportunity to qualification stage."""
        opportunity.stage = opportunity_stages['qualification']
        opportunity.probability = opportunity_stages['qualification'].probability
        opportunity.save()
        
        opportunity.refresh_from_db()
        assert opportunity.stage.name == 'qualification'
        assert opportunity.probability == Decimal('25.00')
    
    def test_move_to_closed_won(self, opportunity, opportunity_stages):
        """Test closing opportunity as won."""
        opportunity.stage = opportunity_stages['closed_won']
        opportunity.probability = Decimal('100.00')
        opportunity.closed_date = timezone.now().date()
        opportunity.save()
        
        opportunity.refresh_from_db()
        assert opportunity.stage.is_won is True
        assert opportunity.closed_date is not None
    
    def test_move_to_closed_lost(self, opportunity, opportunity_stages):
        """Test closing opportunity as lost."""
        opportunity.stage = opportunity_stages['closed_lost']
        opportunity.probability = Decimal('0.00')
        opportunity.closed_date = timezone.now().date()
        opportunity.save()
        
        opportunity.refresh_from_db()
        assert opportunity.stage.is_lost is True
        assert opportunity.closed_date is not None


@pytest.mark.django_db
class TestOpportunityTraits:
    """Tests for opportunity factory traits."""
    
    def test_large_deal_trait(self, account, opportunity_stage_prospecting):
        """Test large deal trait sets correct amount."""
        opp = OpportunityFactory.create(
            account=account,
            stage=opportunity_stage_prospecting,
            large_deal=True,
            tenant_id=account.tenant.tenant_id
        )
        assert opp.amount >= Decimal('500000.00')
    
    def test_small_deal_trait(self, account, opportunity_stage_prospecting):
        """Test small deal trait sets correct amount."""
        opp = OpportunityFactory.create(
            account=account,
            stage=opportunity_stage_prospecting,
            small_deal=True,
            tenant_id=account.tenant.tenant_id
        )
        assert opp.amount <= Decimal('10000.00')
    
    def test_urgent_deal_trait(self, account, opportunity_stage_prospecting):
        """Test urgent deal has soon closing date."""
        opp = OpportunityFactory.create(
            account=account,
            stage=opportunity_stage_prospecting,
            urgent=True,
            tenant_id=account.tenant.tenant_id
        )
        days_until_close = (opp.expected_closing_date - timezone.now().date()).days
        assert days_until_close <= 7


@pytest.mark.django_db
class TestOpportunityBatch:
    """Tests for batch opportunity operations."""
    
    def test_opportunities_batch_creation(self, opportunities_batch):
        """Test batch creation creates correct number."""
        assert len(opportunities_batch) == 10
    
    def test_batch_same_account(self, opportunities_batch, account):
        """Test all batch opportunities have same account."""
        for opp in opportunities_batch:
            assert opp.account == account
    
    def test_batch_unique_names(self, opportunities_batch):
        """Test batch opportunities have unique names."""
        names = [opp.opportunity_name for opp in opportunities_batch]
        assert len(names) == len(set(names))
    
    def test_batch_total_value(self, opportunities_batch):
        """Test calculating total pipeline value."""
        total = sum(opp.amount for opp in opportunities_batch)
        assert total > 0
    
    def test_batch_weighted_value(self, opportunities_batch):
        """Test calculating total weighted pipeline value."""
        weighted_total = sum(opp.weighted_value for opp in opportunities_batch)
        raw_total = sum(opp.amount for opp in opportunities_batch)
        # Weighted should be less than or equal to raw
        assert weighted_total <= raw_total
