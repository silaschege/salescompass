
import csv
from io import StringIO
from typing import List, Dict, Tuple
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.utils import timezone
import json
from datetime import datetime

from core.models import User
from .models import Account, Contact
from leads.models import Lead
from opportunities.models import Opportunity, OpportunityStage
from cases.models import Case
from communication.models import Email, CallLog, Meeting
from engagement.models import EngagementEvent

 
INDUSTRY_CHOICES = {choice[0] for choice in [
    ('tech', 'Technology'),
    ('manufacturing', 'Manufacturing'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('retail', 'Retail'),
    ('energy', 'Energy'),
    ('education', 'Education'),
    ('other', 'Other'),
]}

TIER_CHOICES = {'bronze', 'silver', 'gold', 'platinum'}
ESG_CHOICES = {'low', 'medium', 'high'}

def parse_accounts_csv(file, user) -> Tuple[List[Dict], List[str]]:
    """
    Parse CSV and return list of row dicts + list of errors.
    User is used to scope account visibility (for bulk import validation).
    """
    errors = []
    rows = []

    # Read file
    if hasattr(file, 'read'):
        content = file.read().decode('utf-8')
    else:
        content = file

    reader = csv.DictReader(StringIO(content))
    headers = reader.fieldnames or []

    # Validate headers
    REQUIRED_FIELDS = {'name', 'industry', 'country'}
    ALLOWED_FIELDS = REQUIRED_FIELDS | {
        'tier', 'website', 'address', 'esg_engagement', 'sustainability_goals',
        'renewal_date', 'gdpr_consent', 'ccpa_consent'
    }

    missing_required = REQUIRED_FIELDS - set(headers)
    if missing_required:
        errors.append(f"Missing required columns: {', '.join(missing_required)}")
        return rows, errors

    unknown_fields = set(headers) - ALLOWED_FIELDS
    if unknown_fields:
        errors.append(f"Unknown columns (ignored): {', '.join(unknown_fields)}")

    # Parse rows
    for i, row in enumerate(reader, start=2):
        try:
            cleaned_row = _clean_row(row, i)
            rows.append(cleaned_row)
        except ValidationError as e:
            errors.append(f"Row {i}: {e.message}")
        except Exception as e:
            errors.append(f"Row {i}: Unexpected error: {str(e)}")

    return rows, errors


def _clean_row(row: Dict[str, str], row_num: int) -> Dict[str, any]:
    """Clean and validate a single row."""
    cleaned = {}

    # Required fields
    for field in ['name', 'industry', 'country']:
        value = row.get(field, '').strip()
        if not value:
            raise ValidationError(f"'{field}' is required")
        cleaned[field] = value

    # Optional fields with validation
    if 'tier' in row:
        tier = row['tier'].strip().lower()
        if tier and tier not in TIER_CHOICES:
            raise ValidationError(f"Invalid tier: {tier}. Must be one of: {', '.join(TIER_CHOICES)}")
        cleaned['tier'] = tier or 'bronze'

    if 'industry' in cleaned:
        industry = cleaned['industry'].lower()
        if industry not in INDUSTRY_CHOICES:
            raise ValidationError(f"Invalid industry: {industry}")
        cleaned['industry'] = industry

    if 'esg_engagement' in row:
        esg = row['esg_engagement'].strip().lower()
        if esg and esg not in ESG_CHOICES:
            raise ValidationError(f"Invalid ESG engagement: {esg}. Must be low/medium/high")
        cleaned['esg_engagement'] = esg or 'low'

    # Boolean fields
    for bool_field in ['gdpr_consent', 'ccpa_consent']:
        if bool_field in row:
            val = row[bool_field].strip().lower()
            cleaned[bool_field] = val in ('true', '1', 'yes', 'on')

    # Date field
    if 'renewal_date' in row and row['renewal_date'].strip():
        try:
            datetime.strptime(row['renewal_date'].strip(), '%Y-%m-%d')
            cleaned['renewal_date'] = row['renewal_date'].strip()
        except ValueError:
            raise ValidationError("Invalid renewal_date format. Use YYYY-MM-DD")

    return cleaned

def pprint(value):
    """Pretty print JSON/dict for templates."""
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    return str(value)


def calculate_account_health(account, detailed=False):
    """
    Calculate account health score without saving to database.
    Useful for real-time calculations in views.
    Returns either just the score or a detailed breakdown dict.
    """
    score = 50.0  # Base score
    
    # Engagement metrics (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    recent_emails = Email.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
    recent_calls = CallLog.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
    recent_meetings = Meeting.objects.filter(account=account, timestamp__gte=thirty_days_ago).count()
    
    engagement_score = min(20, recent_emails * 2) + min(15, recent_calls * 5) + min(15, recent_meetings * 10)
    score += engagement_score
    
    # Support cases
    open_cases = Case.objects.filter(
        account=account, 
        status__in=['new', 'open', 'escalated']
    )
    
    case_penalty = 0
    for case in open_cases:
        if case.priority == 'critical':
            case_penalty += 20
        elif case.priority == 'high':
            case_penalty += 10
        else:
            case_penalty += 2
            
    score -= case_penalty
    
    # Renewal risk
    renewal_penalty = 0
    days_to_renewal = None
    if account.renewal_date:
        days_to_renewal = (account.renewal_date - timezone.now().date()).days
        if days_to_renewal < 30 and score < 70:
            renewal_penalty = 10
            
    score -= renewal_penalty
    
    # Account completeness
    completeness_score = 0
    if account.website:
        completeness_score += 10
    if account.phone:
        completeness_score += 5
    if account.industry:
        completeness_score += 5
        
    score += completeness_score
    
    # Recent updates
    update_bonus = 0
    if hasattr(account, 'updated_at') and account.updated_at:
        days_since_update = (timezone.now() - account.updated_at).days
        if days_since_update < 7:
            update_bonus += 5
        elif days_since_update < 30:
            update_bonus += 2
        elif days_since_update > 90:
            update_bonus -= 5
            
    score += update_bonus
    
    # Cap score
    score = max(0.0, min(100.0, score))
    
    if detailed:
        return {
            'total_score': score,
            'engagement_score': engagement_score,
            'case_penalty': case_penalty,
            'renewal_penalty': renewal_penalty,
            'completeness_score': completeness_score,
            'update_bonus': update_bonus,
            'recent_emails': recent_emails,
            'recent_calls': recent_calls,
            'recent_meetings': recent_meetings,
            'open_cases_count': open_cases.count(),
            'renewal_days': days_to_renewal
        }
    
    return score


def get_accounts_summary(tenant_id=None):
    """Get summary statistics for all accounts"""
    accounts = Account.objects.all()
    if tenant_id:
        accounts = accounts.filter(tenant_id=tenant_id)
    
    total_accounts = accounts.count()
    active_accounts = accounts.filter(status='active').count()
    at_risk_accounts = accounts.filter(status='at_risk').count()
    churned_accounts = accounts.filter(status='churned').count()
    
    # Engagement metrics
    recent_engagement = EngagementEvent.objects.filter(
        account_company_id__in=accounts.values_list('id', flat=True),
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Lead metrics
    open_leads = Lead.objects.filter(
        account_id__in=accounts.values_list('id', flat=True),
        status__in=['new', 'contacted', 'qualified']
    ).count()
    
    # Case metrics
    open_cases = Case.objects.filter(
        account_id__in=accounts.values_list('id', flat=True),
        status__in=['new', 'open', 'escalated']
    ).count()
    
    return {
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'at_risk_accounts': at_risk_accounts,
        'churned_accounts': churned_accounts,
        'recent_engagement': recent_engagement,
        'open_leads': open_leads,
        'open_cases': open_cases
    }


def get_last_engagement_date(account):
    """Get the date of the most recent engagement with an account"""
    latest_events = []
    
    # Get latest communication events
    latest_email = Email.objects.filter(account=account).order_by('-timestamp').first()
    latest_call = CallLog.objects.filter(account=account).order_by('-timestamp').first()
    latest_meeting = Meeting.objects.filter(account=account).order_by('-timestamp').first()
    
    # Get latest engagement event
    latest_engagement = EngagementEvent.objects.filter(
        account_company=account
    ).order_by('-created_at').first()
    
    # Compare all dates
    for event in [latest_email, latest_call, latest_meeting, latest_engagement]:
        if event:
            if hasattr(event, 'timestamp'):
                latest_events.append(event.timestamp)
            else:
                latest_events.append(event.created_at)
    
    return max(latest_events) if latest_events else None


def get_account_kpi_data(account):
    """Get KPI data for an account for dashboard display"""
    # Date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    ninety_days_ago = today - timezone.timedelta(days=90)
    
    # Engagement metrics
    recent_engagement = EngagementEvent.objects.filter(
        account_company=account,
        created_at__gte=thirty_days_ago
    ).count()
    
    quarterly_engagement = EngagementEvent.objects.filter(
        account_company=account,
        created_at__gte=ninety_days_ago
    ).count()
    
    # Lead metrics
    open_leads = Lead.objects.filter(
        account=account,
        status__in=['new', 'contacted', 'qualified']
    ).count()
    
    converted_leads = Lead.objects.filter(
        account=account,
        status='converted'
    ).count()
    
    # Opportunity metrics
    open_opportunities = Opportunity.objects.filter(
        account=account,
        stage__opportunity_stage_name__in=['prospecting', 'qualification', 'needs_analysis']
    ).count()
    
    high_value_opportunities = Opportunity.objects.filter(
        account=account,
        stage__opportunity_stage_name__in=['prospecting', 'qualification', 'needs_analysis'],
        amount__gte=50000  # High-value threshold
    ).count()
    
    # Case metrics
    open_cases = Case.objects.filter(
        account=account,
        status__in=['new', 'open', 'escalated']
    ).count()
    
    return {
        'account': account,
        'recent_engagement': recent_engagement,
        'quarterly_engagement': quarterly_engagement,
        'open_leads': open_leads,
        'converted_leads': converted_leads,
        'open_opportunities': open_opportunities,
        'high_value_opportunities': high_value_opportunities,
        'open_cases': open_cases,
        'health_score': calculate_account_health(account),
        'last_engagement': get_last_engagement_date(account)
    }


def get_account_health_history(account, days=90):
    """Get historical health scores for an account over a time period"""
    today = timezone.now().date()
    health_history = []
    
    for i in range(days):
        date = today - timezone.timedelta(days=i)
        try:
            engagement = EngagementEvent.objects.filter(
                account_company=account,
                created_at__date=date
            ).count()
            
            score = 50.0 + (engagement * 2)
            score = max(0, min(100, score))
            
            health_history.append({
                'date': date,
                'score': score,
                'engagement': engagement
            })
        except Exception:
            health_history.append({
                'date': date,
                'score': 50.0,
                'engagement': 0
            })
    
    health_history.reverse()
    return health_history


def calculate_account_engagement_score(account, tenant_id=None):
    """Calculate engagement score with multi-tenant support"""
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    # Base engagement score from events
    base_score = EngagementEvent.objects.filter(
        account_company=account,
        created_at__gte=thirty_days_ago
    ).count() * 2  # 2 points per event
    
    # Add points for recent activity
    recent_event = EngagementEvent.objects.filter(
        account_company=account
    ).order_by('-created_at').first()
    
    if recent_event:
        days_since_last = (timezone.now() - recent_event.created_at).days
        if days_since_last < 7:
            base_score += 10
        elif days_since_last < 14:
            base_score += 5
    
    # Cap at 100
    score = min(100, base_score)
    
    return score


def get_quarter_date_range(year, month):
    """Get start and end dates for the quarter containing the given month/year"""
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
        
    quarter = (month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1
    
    start_date = datetime(year, start_month, 1).date()
    
    next_quarter_month = start_month + 3
    next_quarter_year = year
    if next_quarter_month > 12:
        next_quarter_month = 1
        next_quarter_year += 1
    
    end_date = datetime(next_quarter_year, next_quarter_month, 1).date() - timezone.timedelta(days=1)
    
    return start_date, end_date


def calculate_revenue_trend(revenue_data):
    """Calculate revenue trend based on historical data"""
    if not revenue_data:
        return 0
        
    # Simple trend calculation: compare most recent quarter to average of previous
    recent_value = revenue_data[-1]['value'] if revenue_data else 0
    if len(revenue_data) <= 1:
        return 0 if recent_value == 0 else 100
        
    previous_values = [item['value'] for item in revenue_data[:-1]]
    average_previous = sum(previous_values) / len(previous_values) if previous_values else 0
    
    if average_previous == 0:
        return 0 if recent_value == 0 else 100
    
    return ((recent_value - average_previous) / average_previous) * 100


def calculate_win_rate(open_opportunities, closed_won):
    """Calculate win rate based on opportunities and closed deals"""
    open_count = open_opportunities.count() if hasattr(open_opportunities, 'count') else len(open_opportunities)
    closed_count = closed_won.count() if hasattr(closed_won, 'count') else len(closed_won)
    
    if open_count + closed_count == 0:
        return 0
        
    return (closed_count / (open_count + closed_count)) * 100


def analyze_account_revenue(account):
    """Analyze account revenue data including opportunities"""
    # Current opportunities
    open_opportunities = Opportunity.objects.filter(
        account=account,
        stage__opportunity_stage_name__in=['prospecting', 'qualification', 'needs_analysis']
    )
    
    closed_won = Opportunity.objects.filter(
        account=account,
        stage__opportunity_stage_name='Closed Won'
    )
    
    # Revenue pipeline analysis
    total_pipeline_value = sum(opportunity.amount for opportunity in open_opportunities if opportunity.amount)
    total_closed_value = sum(opportunity.amount for opportunity in closed_won if opportunity.amount)
    
    # Historical revenue analysis
    historical_revenue = []
    current_date = timezone.now().date()
    for i in range(4):  # Last 4 quarters
        quarter_start, quarter_end = get_quarter_date_range(current_date.year, current_date.month - (i * 3))
        
        quarterly_won = Opportunity.objects.filter(
            account=account,
            stage__opportunity_stage_name='Closed Won',
            updated_at__date__range=[quarter_start, quarter_end]
        )
        
        quarterly_value = sum(opp.amount for opp in quarterly_won if opp.amount)
        
        historical_revenue.append({
            'quarter': f"Q{(quarter_start.month - 1) // 3 + 1} {quarter_start.year}",
            'value': float(quarterly_value),
            'deal_count': quarterly_won.count()
        })
    
    historical_revenue.reverse()
    
    return {
        'total_pipeline_value': total_pipeline_value,
        'total_closed_value': total_closed_value,
        'historical_revenue': historical_revenue,
        'win_rate': calculate_win_rate(open_opportunities, closed_won),
        'revenue_trend': calculate_revenue_trend(historical_revenue)
    }


def get_account_analytics_data(account):
    """Get comprehensive analytics data for an account"""
    # Date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    
    # Engagement data
    recent_engagement = EngagementEvent.objects.filter(
        account_company=account,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:5]
    
    engagement_trend = []
    for i in range(30):
        date = today - timezone.timedelta(days=i)
        count = EngagementEvent.objects.filter(
            account_company=account,
            created_at__date=date
        ).count()
        engagement_trend.append({
            'date': date,
            'count': count
        })
    engagement_trend.reverse()
    
    # Lead pipeline
    lead_pipeline = Lead.objects.filter(account=account).values('status').annotate(count=Count('id'))
    
    # Opportunities
    opportunities = Opportunity.objects.filter(account=account).order_by('-amount')
    
    # Case history
    case_history = Case.objects.filter(account=account).order_by('-created_at')[:5]
    
    return {
        'recent_engagement': recent_engagement,
        'engagement_trend': engagement_trend,
        'lead_pipeline': lead_pipeline,
        'opportunities': opportunities,
        'case_history': case_history,
        'health_history': get_account_health_history(account),
        'engagement_score': calculate_account_engagement_score(account),
        'revenue_analysis': analyze_account_revenue(account),
        'account_leads': Lead.objects.filter(account=account),
        'account_opportunities': Opportunity.objects.filter(account=account)
    }


def get_top_performing_accounts(limit=5):
    """Get top performing accounts based on revenue and health"""
    # Filter for accounts with closed_won opportunities
    top_accounts_qs = Account.objects.annotate(
        revenue=Sum('opportunities__amount', filter=Q(opportunities__stage__opportunity_stage_name='Closed Won'))
    ).order_by('-revenue')[:limit]
    
    results = []
    for account in top_accounts_qs:
        if account.revenue:
            results.append({
                'account': account,
                'revenue': account.revenue,
                'engagement_score': calculate_account_engagement_score(account),
                'health_score': getattr(account, 'health_score', 0)
            })
    
    return results
