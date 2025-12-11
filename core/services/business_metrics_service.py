"""
Service layer for business metrics calculations
"""
from django.db.models import Avg, Sum, Count
from core.models import User
from leads.models import Lead
from opportunities.models import Opportunity
from marketing.models import Campaign
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class BusinessMetricsService:
    """
    Service class for calculating business metrics like CLV, CAC, and sales velocity
    """
    
    @staticmethod
    def calculate_clv_metrics(tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate Customer Lifetime Value metrics
        """
        users = User.objects.all()
        if tenant_id:
            users = users.filter(tenant_id=tenant_id)
        
        avg_clv = users.aggregate(avg_clv=Avg('customer_lifetime_value'))['avg_clv'] or 0
        total_clv = users.aggregate(total_clv=Sum('customer_lifetime_value'))['total_clv'] or 0
        avg_order_value = users.aggregate(avg_order=Avg('avg_order_value'))['avg_order'] or 0
        avg_purchase_frequency = users.aggregate(avg_freq=Avg('purchase_frequency'))['avg_freq'] or 0
        
        return {
            'avg_clv': float(avg_clv),
            'total_clv': float(total_clv),
            'avg_order_value': float(avg_order_value),
            'avg_purchase_frequency': float(avg_purchase_frequency),
        }
    
    @staticmethod
    def calculate_cac_metrics(tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate Customer Acquisition Cost metrics
        """
        campaigns = Campaign.objects.all()
        if tenant_id:
            campaigns = campaigns.filter(tenant_id=tenant_id)
        
        total_spend = sum([campaign.actual_cost or 0 for campaign in campaigns])
        
        leads = Lead.objects.all()
        if tenant_id:
            leads = leads.filter(tenant_id=tenant_id)
        
        new_customers_count = leads.filter(status='converted').count()
        
        avg_cac = 0
        if new_customers_count > 0:
            avg_cac = total_spend / new_customers_count
        
        conversion_rate = (new_customers_count / leads.count() * 100) if leads.count() > 0 else 0
        
        return {
            'avg_cac': float(avg_cac),
            'total_spend': float(total_spend),
            'new_customers_count': new_customers_count,
            'conversion_rate': float(conversion_rate),
        }
    
    @staticmethod
    def calculate_sales_velocity_metrics(tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate sales velocity metrics
        """
        opportunities = Opportunity.objects.all()
        if tenant_id:
            opportunities = opportunities.filter(tenant_id=tenant_id)
        
        total_velocity = 0
        for opp in opportunities:
            total_velocity += opp.calculate_sales_velocity()
        avg_sales_velocity = total_velocity / opportunities.count() if opportunities.count() > 0 else 0
        
        total_opportunities = opportunities.count()
        won_opportunities = opportunities.filter(stage__is_won=True).count()
        conversion_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
        
        # Calculate average sales cycle
        avg_sales_cycle = 0
        if won_opportunities > 0:
            avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in opportunities.filter(stage__is_won=True)) / won_opportunities
        else:
            open_opps = opportunities.filter(stage__is_won=False)
            if open_opps.count() > 0:
                avg_sales_cycle = sum(opp.calculate_average_sales_cycle() for opp in open_opps) / open_opps.count()
        
        return {
            'avg_sales_velocity': float(avg_sales_velocity),
            'conversion_rate': float(conversion_rate),
            'avg_sales_cycle': float(avg_sales_cycle),
        }
    
    @staticmethod
    def calculate_roi_metrics(tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate Return on Investment metrics
        """
        users = User.objects.all()
        if tenant_id:
            users = users.filter(tenant_id=tenant_id)
        
        total_clv = users.aggregate(total_clv=Sum('customer_lifetime_value'))['total_clv'] or 0
        total_cac = users.aggregate(total_cac=Sum('acquisition_cost'))['total_cac'] or 0
        
        roi = 0
        if total_cac > 0:
            roi = (total_clv - total_cac) / total_cac
        
        return {
            'total_clv': float(total_clv),
            'total_cac': float(total_cac),
            'roi': float(roi),
        }
    
    @staticmethod
    def calculate_conversion_funnel_metrics(tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate conversion funnel metrics from lead to opportunity to customer
        """
        leads = Lead.objects.all()
        opportunities = Opportunity.objects.all()
        
        if tenant_id:
            leads = leads.filter(tenant_id=tenant_id)
            opportunities = opportunities.filter(tenant_id=tenant_id)
        
        total_leads = leads.count()
        qualified_leads = leads.filter(status='qualified').count()
        converted_leads = leads.filter(status='converted').count()
        
        total_opportunities = opportunities.count()
        won_opportunities = opportunities.filter(stage__is_won=True).count()
        
        lead_to_qualified_rate = (qualified_leads / total_leads * 10) if total_leads > 0 else 0
        lead_to_customer_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        opp_to_won_rate = (won_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
        
        return {
            'total_leads': total_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'total_opportunities': total_opportunities,
            'won_opportunities': won_opportunities,
            'lead_to_qualified_rate': float(lead_to_qualified_rate),
            'lead_to_customer_rate': float(lead_to_customer_rate),
            'opp_to_won_rate': float(opp_to_won_rate),
        }
    
    @staticmethod
    def calculate_metrics_trend(days: int = 30, tenant_id: Optional[str] = None) -> Dict:
        """
        Calculate metrics trends over a specified period
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate daily metrics
        date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        daily_metrics = []
        for date in date_range:
            # Get metrics for this specific date
            leads = Lead.objects.filter(created_at__date=date)
            opportunities = Opportunity.objects.filter(created_at__date=date)
            
            if tenant_id:
                leads = leads.filter(tenant_id=tenant_id)
                opportunities = opportunities.filter(tenant_id=tenant_id)
            
            daily_metrics.append({
                'date': date,
                'new_leads': leads.count(),
                'new_opportunities': opportunities.count(),
            })
        
        return {
            'date_range': date_range,
            'daily_metrics': daily_metrics,
        }
