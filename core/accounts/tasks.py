from celery import shared_task
import csv
from io import StringIO
from typing import List, Dict, Tuple
from django.core.exceptions import ValidationError
from core.models import User

from django.db.models import Count, Q
from .models import Account, Contact
from leads.models import Lead
from opportunities.models import Opportunity
from cases.models import Case
from communication.models import Email, CallLog, Meeting
from django.utils import timezone
import json
from celery import shared_task

@shared_task
def update_account_health(account_id):
    """
    Calculate and update the health score for a single account.
    Score (0-100) based on:
    - Engagement (Last 30 days emails/calls)
    - Support Cases (Open high priority cases reduce score)
    - NPS (if available)
    - Account activity and completeness
    """
    try:
        account = Account.objects.get(id=account_id)
        score = 50.0 # Start neutral
        
        # 1. Engagement (Last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        recent_emails = Email.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        recent_calls = CallLog.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        recent_meetings = Meeting.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
        
        # Add points for engagement
        score += min(20, recent_emails * 2)
        score += min(15, recent_calls * 5)
        score += min(15, recent_meetings * 10)
        
        # 2. Support Cases (Risk Factor)
        open_cases = Case.objects.filter(
            account=account, 
            status__in=['new', 'open', 'escalated']
        )
        
        for case in open_cases:
            if case.priority == 'critical':
                score -= 20
            elif case.priority == 'high':
                score -= 10
            else:
                score -= 2
                
        # 3. Renewal Risk
        if account.renewal_date:
            days_to_renewal = (account.renewal_date - timezone.now().date()).days
            if days_to_renewal < 30 and score < 70:
                # High risk if renewal is close and health is low
                score -= 10
                
        # 4. Account completeness
        completeness_score = 0
        if account.website:
            completeness_score += 10
        if account.phone:
            completeness_score += 5
        if account.industry:
            completeness_score += 5
            
        score += completeness_score
        
        # 5. Recent account updates
        if account.last_modified_at:
            days_since_update = (timezone.now() - account.last_modified_at).days
            if days_since_update < 7:
                score += 5
            elif days_since_update < 30:
                score += 2
            elif days_since_update > 90:
                score -= 5
        
        # Cap score
        account.health_score = max(0.0, min(100.0, score))
        
        # Update status based on health
        if account.health_score < 40:
            account.status = 'at_risk'
        elif account.health_score > 70:
            account.status = 'active' # or 'healthy'
        else:
            account.status = 'neutral'
            
        account.save(update_fields=['health_score', 'status'])
        
        return account.health_score
        
    except Account.DoesNotExist:
        return None
    except Exception as e:
        print(f"Error updating account health: {e}")
        return None

@shared_task
def update_all_account_health():
    """
    Periodic task to update health for all active accounts.
    """
    for account in Account.objects.filter(status__in=['active', 'at_risk']):
        update_account_health.delay(account.id)


@shared_task(queue='sales')
def send_account_health_alert(account_id):
    """Send alert if account health score drops below threshold"""
    try:
        account = Account.objects.get(id=account_id)
        health_score = account.health_score if account.health_score is not None else 0
        
        if health_score < 40:  # At-risk threshold
            # Get account contacts
            primary_contact = account.contacts.filter(is_primary=True).first()
            
            # Prepare alert context
            context = {
                'account': account,
                'health_score': health_score,
                'primary_contact': primary_contact,
                'owner': account.owner,
                'reason': 'Account health score dropped below 40'
            }
            
            # Send alert to account owner
            if account.owner:
                # In a real implementation, this would use a proper email service
                print(f"Sending alert to {account.owner.email}: Account {account.name} health is at-risk")
                
            # Additional alerting logic could be implemented here
            # - Send SMS
            # - Create a task for account manager
            # - Trigger a webhook
            
        return True
        
    except Account.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending account health alert: {e}")
        return False


@shared_task(queue='sales')
def send_account_renewal_reminder(account_id):
    """Send renewal reminder when account is approaching renewal date"""
    try:
        account = Account.objects.get(id=account_id)
        
        if account.renewal_date:
            days_to_renewal = (account.renewal_date - timezone.now().date()).days
            
            if days_to_renewal == 30:  # 30 days before renewal
                # Prepare renewal reminder context
                context = {
                    'account': account,
                    'days_to_renewal': days_to_renewal,
                    'renewal_date': account.renewal_date
                }
                
                # Send reminder to account owner
                if account.owner:
                    # In a real implementation, this would use a proper email service
                    print(f"Sending renewal reminder to {account.owner.email}: Account {account.name} renews in 30 days")
                    
                # Additional reminder logic could be implemented here
                
        return True
        
    except Account.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending account renewal reminder: {e}")
        return False


@shared_task(queue='sales')
def batch_update_account_health(account_ids):
    """Update health scores for multiple accounts in batch"""
    results = []
    for account_id in account_ids:
        result = update_account_health.delay(account_id)
        results.append({
            'account_id': account_id,
            'result': result
        })
    
    return results


@shared_task(queue='sales')
def send_account_engagement_alert(account_id):
    """Send alert if account engagement drops below threshold"""
    try:
        account = Account.objects.get(id=account_id)
        engagement_score = calculate_account_engagement_score(account)
        
        if engagement_score < 30:  # Low engagement threshold
            # Get account contacts
            primary_contact = account.contacts.filter(is_primary=True).first()
            
            # Prepare alert context
            context = {
                'account': account,
                'engagement_score': engagement_score,
                'primary_contact': primary_contact,
                'owner': account.owner,
                'reason': 'Account engagement score dropped below 30'
            }
            
            # Send alert to account owner
            if account.owner:
                # In a real implementation, this would use a proper email service
                print(f"Sending engagement alert to {account.owner.email}: Account {account.name} engagement is low")
                
            # Create a task for account manager
            # This would use the tasks module in a real implementation
            
        return True
        
    except Account.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error sending account engagement alert: {e}")
        return False


@shared_task(queue='sales')
def send_account_summary_report(account_id):
    """Send a summary report of account health, engagement and revenue"""
    try:
        account = Account.objects.get(id=account_id)
        
        # Get account analytics data
        analytics_data = get_account_analytics_data(account)
        
        # Prepare report data
        report_data = {
            'account': account,
            'health_score': account.health_score if account.health_score is not None else 0,
            'engagement_score': calculate_account_engagement_score(account),
            'total_pipeline_value': analytics_data['revenue_analysis']['total_pipeline_value'],
            'total_closed_value': analytics_data['revenue_analysis']['total_closed_value'],
            'win_rate': analytics_data['revenue_analysis']['win_rate'],
            'engagement_trend': [item['count'] for item in analytics_data['engagement_trend']]
        }
        
        # Generate and send report
        # In a real implementation, this would generate a PDF report and send it via email
        print(f"Generated account summary report for {account.account_name}")
        
        return True
        
    except Account.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error generating account summary report: {e}")
        return False