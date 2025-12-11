from django.db.models import Avg, Sum, Count
from django.utils import timezone
from django.db import models
from .models import Lead, MarketingChannel


class LeadScoringService:
    """
    Service class for lead scoring operations and intelligence.
    """
    
    @staticmethod
    def calculate_lead_score(lead):
        """
        Recalculate the entire lead score based on profile, interactions, and business metrics.
        """
        score = 0
        
        # 1. Profile Completeness (Max 40 points)
        if lead.email: score += 10
        if lead.phone: score += 10
        if lead.job_title: score += 5
        if lead.company: score += 5
        if lead.industry: score += 5
        if lead.lead_description: score += 5
        
        # 2. Business Metrics Scoring (Max 30 points)
        if lead.company_size:
            if lead.company_size >= 1000:  # Enterprise
                score += 15
            elif lead.company_size >= 100:  # Mid-market
                score += 10
            elif lead.company_size >= 10:  # SMB
                score += 5
        
        if lead.annual_revenue:
            revenue = float(lead.annual_revenue)
            if revenue >= 10000000:  # $10M+
                score += 15
            elif revenue >= 1000000:  # $1M+
                score += 10
            elif revenue >= 100000:  # $100K+
                score += 5
        
        # Funding stage scoring
        high_funding_stages = ['Series A', 'Series B', 'Series C', 'IPO', 'Public']
        if lead.funding_stage in high_funding_stages:
            score += 10
        elif lead.funding_stage == 'Seed':
            score += 5
            
        # Business type scoring
        if lead.business_type == 'B2B':
            score += 5
        
        # Cap at 100
        lead.lead_score = max(0, min(100, score))
        lead.save(update_fields=['lead_score'])
        
        # Trigger status update based on score
        lead.update_status_from_score()
        
        return lead.lead_score

    @staticmethod
    def get_next_best_action(lead):
        """
        Determine the Next Best Action (NBA) for a lead.
        """
        # 1. Status-based actions
        if lead.status == 'new':
            return {
                "action": "Qualify Lead",
                "description": "Review profile and initial data to determine fit.",
                "icon": "bi-check-circle",
                "priority": "high"
            }
            
        if lead.status == 'qualified' and lead.lead_score > 70:
            return {
                "action": "Convert to Opportunity",
                "description": "Lead score is high. Convert to deal now.",
                "icon": "bi-currency-dollar",
                "priority": "critical"
            }

        # 2. Time-based actions
        if lead.lead_acquisition_date:
            days_since_acquisition = (timezone.now() - lead.lead_acquisition_date).days
            if days_since_acquisition > 14:
                return {
                    "action": "Re-engage Lead",
                    "description": f"No activity in {days_since_acquisition} days. Send a check-in email.",
                    "icon": "bi-envelope",
                    "priority": "medium"
                }
            elif days_since_acquisition > 7:
                return {
                    "action": "Follow Up",
                    "description": "It's been a week. Give them a call.",
                    "icon": "bi-telephone",
                    "priority": "medium"
                }

        # 3. Default
        return {
            "action": "Log Interaction",
            "description": "Record a call, email, or meeting to build history.",
            "icon": "bi-pencil-square",
            "priority": "low"
        }

    @staticmethod
    def get_scoring_recommendations(lead):
        """
        Get recommendations for improving lead score.
        """
        recommendations = []
        
        if not lead.email: 
            recommendations.append("Add email address (+10 points)")
        if not lead.phone: 
            recommendations.append("Add phone number (+10 points)")
        if not lead.job_title: 
            recommendations.append("Add job title (+5 points)")
        if not lead.lead_description: 
            recommendations.append("Add lead description (+5 points)")
        
        # Business information recommendations
        if not lead.company_size:
            recommendations.append("Add company size (+5-15 points)")
        if not lead.annual_revenue:
            recommendations.append("Add annual revenue (+5-15 points)")
        
        return recommendations


class CACCalculationService:
    """
    Service class for Customer Acquisition Cost (CAC) calculations and analytics.
    """
    
    @staticmethod
    def calculate_cac_for_lead(lead):
        """
        Calculate CAC for a specific lead
        """
        if lead.cac_cost:
            return float(lead.cac_cost)
        return 0.0
    
    @staticmethod
    def calculate_average_cac_by_channel(marketing_channel, tenant_id=None, use_ref=False):
        """
        Calculate average CAC for a specific marketing channel
        """
        if use_ref:
            # Filter by marketing channel reference (new field)
            queryset = Lead.objects.filter(marketing_channel_ref__channel_name=marketing_channel)
        else:
            # Filter by marketing channel (legacy field)
            queryset = Lead.objects.filter(marketing_channel=marketing_channel)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        result = queryset.aggregate(
            avg_cac=Avg('cac_cost'),
            total_leads=Count('id'),
            total_cac=Sum('cac_cost')
        )
        
        return {
            'channel': marketing_channel,
            'average_cac': float(result['avg_cac'] or 0),
            'total_leads': result['total_leads'],
            'total_cac_spent': float(result['total_cac'] or 0)
        }

    @staticmethod
    def calculate_average_cac_by_channel_ref(marketing_channel_ref_id, tenant_id=None):
        """
        Calculate average CAC for a specific marketing channel reference
        """
        queryset = Lead.objects.filter(marketing_channel_ref_id=marketing_channel_ref_id)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        result = queryset.aggregate(
            avg_cac=Avg('cac_cost'),
            total_leads=Count('id'),
            total_cac=Sum('cac_cost')
        )
        
        # Get channel name for the response
        try:
            channel = MarketingChannel.objects.get(id=marketing_channel_ref_id)
            channel_name = channel.channel_name
        except MarketingChannel.DoesNotExist:
            channel_name = "Unknown Channel"
        
        return {
            'channel': channel_name,
            'average_cac': float(result['avg_cac'] or 0),
            'total_leads': result['total_leads'],
            'total_cac_spent': float(result['total_cac'] or 0)
        }
    
    @staticmethod
    def calculate_average_cac_by_campaign(campaign_source, tenant_id=None):
        """
        Calculate average CAC for a specific campaign
        """
        queryset = Lead.objects.filter(campaign_source=campaign_source)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        result = queryset.aggregate(
            avg_cac=Avg('cac_cost'),
            total_leads=Count('id'),
            total_cac=Sum('cac_cost')
        )
        
        return {
            'campaign': campaign_source,
            'average_cac': float(result['avg_cac'] or 0),
            'total_leads': result['total_leads'],
            'total_cac_spent': float(result['total_cac'] or 0)
        }
    
    @staticmethod
    def get_cac_by_period(start_date, end_date, tenant_id=None):
        """
        Get CAC totals for a specific period
        """
        queryset = Lead.objects.filter(
            lead_acquisition_date__date__gte=start_date,
            lead_acquisition_date__date__lte=end_date
        )
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        result = queryset.aggregate(
            avg_cac=Avg('cac_cost'),
            total_leads=Count('id'),
            total_cac=Sum('cac_cost')
        )
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'average_cac': float(result['avg_cac'] or 0),
            'total_leads': result['total_leads'],
            'total_cac_spent': float(result['total_cac'] or 0)
        }
    
    @staticmethod
    def get_channel_performance_metrics(tenant_id=None):
        """
        Get performance metrics across all marketing channels (legacy field)
        """
        queryset = Lead.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Get all unique marketing channels
        channels = queryset.values_list('marketing_channel', flat=True).distinct()
        
        channel_metrics = {}
        for channel in channels:
            if not channel:  # Skip empty channels
                continue
            channel_queryset = queryset.filter(marketing_channel=channel)
            result = channel_queryset.aggregate(
                avg_cac=Avg('cac_cost'),
                total_leads=Count('id'),
                total_cac=Sum('cac_cost'),
                converted_leads=Count('id', filter=models.Q(status='converted'))
            )
            
            total_leads = result['total_leads']
            converted_leads = result['converted_leads'] or 0
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            channel_metrics[channel] = {
                'channel': channel,
                'average_cac': float(result['avg_cac'] or 0),
                'total_leads': total_leads,
                'total_cac_spent': float(result['total_cac'] or 0),
                'converted_leads': converted_leads,
                'conversion_rate': conversion_rate
            }
        
        return channel_metrics

    @staticmethod
    def get_channel_performance_metrics_ref(tenant_id=None):
        """
        Get performance metrics across all marketing channels (reference field)
        """
        queryset = Lead.objects.all().select_related('marketing_channel_ref')
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Get all unique marketing channel references
        channel_refs = queryset.exclude(marketing_channel_ref__isnull=True).values_list('marketing_channel_ref_id', flat=True).distinct()
        
        channel_metrics = {}
        for channel_ref_id in channel_refs:
            if not channel_ref_id:  # Skip empty references
                continue
            channel_queryset = queryset.filter(marketing_channel_ref_id=channel_ref_id)
            result = channel_queryset.aggregate(
                avg_cac=Avg('cac_cost'),
                total_leads=Count('id'),
                total_cac=Sum('cac_cost'),
                converted_leads=Count('id', filter=models.Q(status='converted'))
            )
            
            total_leads = result['total_leads']
            converted_leads = result['converted_leads'] or 0
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            # Get channel name for the response
            try:
                channel = MarketingChannel.objects.get(id=channel_ref_id)
                channel_name = channel.channel_name
            except MarketingChannel.DoesNotExist:
                channel_name = "Unknown Channel"
            
            channel_metrics[channel_name] = {
                'channel': channel_name,
                'average_cac': float(result['avg_cac'] or 0),
                'total_leads': total_leads,
                'total_cac_spent': float(result['total_cac'] or 0),
                'converted_leads': converted_leads,
                'conversion_rate': conversion_rate
            }
        
        return channel_metrics
    
    @staticmethod
    def get_campaign_performance_metrics(tenant_id=None):
        """
        Get performance metrics across all campaigns
        """
        queryset = Lead.objects.all()
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        # Get all unique campaigns
        campaigns = queryset.values_list('campaign_source', flat=True).distinct()
        
        campaign_metrics = {}
        for campaign in campaigns:
            if not campaign:  # Skip empty campaign names
                continue
            campaign_queryset = queryset.filter(campaign_source=campaign)
            result = campaign_queryset.aggregate(
                avg_cac=Avg('cac_cost'),
                total_leads=Count('id'),
                total_cac=Sum('cac_cost'),
                converted_leads=Count('id', filter=models.Q(status='converted'))
            )
            
            total_leads = result['total_leads']
            converted_leads = result['converted_leads'] or 0
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            campaign_metrics[campaign] = {
                'campaign': campaign,
                'average_cac': float(result['avg_cac'] or 0),
                'total_leads': total_leads,
                'total_cac_spent': float(result['total_cac'] or 0),
                'converted_leads': converted_leads,
                'conversion_rate': conversion_rate
            }
        
        return campaign_metrics
