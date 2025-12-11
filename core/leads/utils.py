from django.utils import timezone
from datetime import timedelta
from .models import Lead, LeadSourceAnalytics
from core.models import User as  Account
from django.db.models import Avg

def calculate_lead_score(lead: Lead) -> int:
    """
    Auto-calculates lead score (0–100) based on industry, source, and seniority.
    """
    score = 20  # Base score

    # Industry boost (high-value industries)
    high_value_industries = {'tech', 'finance', 'energy'}
    if lead.industry in high_value_industries:
        score += 20

    # Source quality
    source_scores = {
        'event': 30,
        'referral': 25,
        'web': 15,
        'ads': 10,
        'manual': 5
    }
    score += source_scores.get(lead.source, 5)

    # Job title seniority (simple keyword match)
    senior_titles = {'ceo', 'cto', 'director', 'manager', 'head', 'vp', 'president'}
    job_title = lead.job_title.lower() if lead.job_title else ''
    if any(title in job_title for title in senior_titles):
        score += 15

    # Website presence (if phone is provided, assume more serious)
    if lead.phone:
        score += 10

    # Cap at 100
    return min(100, score)


def create_lead_source_analytics(tenant_id: str = None) -> None:
    """
    Create daily analytics snapshot for lead sources.
    """
    today = timezone.now().date()
    leads = Lead.objects.filter(created_at__date=today)
    if tenant_id:
        leads = leads.filter(tenant_id=tenant_id)
    
    # Get unique sources
    sources = leads.values_list('source', flat=True).distinct()
    
    for source in sources:
        source_leads = leads.filter(source=source)
        total = source_leads.count()
        qualified = source_leads.filter(status__in=['qualified', 'converted']).count()
        converted = source_leads.filter(status='converted').count()
        avg_score = source_leads.aggregate(avg=Avg('lead_score'))['avg'] or 0
        
        LeadSourceAnalytics.objects.update_or_create(
            date=today,
            source=source,
            tenant_id=tenant_id,
            defaults={
                'lead_count': total,
                'qualified_count': qualified,
                'converted_count': converted,
                'avg_lead_score': round(avg_score, 2)
            }
        )


def process_web_to_lead_submission(form_config, cleaned_data, ip_address=None):
    """
    Process a web-to-lead form submission.
    """
    # Create lead
    lead_data = {
        'first_name': cleaned_data.get('first_name', ''),
        'last_name': cleaned_data.get('last_name', ''),
        'email': cleaned_data.get('email', ''),
        'phone': cleaned_data.get('phone', ''),
        'company': cleaned_data.get('company', ''),
        'industry': cleaned_data.get('industry', 'other'),
        'job_title': cleaned_data.get('job_title', ''),
        'source': 'web',
        'tenant_id': form_config.tenant_id
    }
    
    lead = Lead.objects.create(**lead_data)
    lead.lead_score = calculate_lead_score(lead)
    lead.save(update_fields=['lead_score'])
    
    # Assign owner
    if form_config.assign_to:
        lead.owner = form_config.assign_to
        lead.save(update_fields=['owner'])
    elif form_config.assign_to_role:
        # Find user with role (simplified)
        from core.models import User
        potential_owner = User.objects.filter(
            role__name=form_config.assign_to_role,
            tenant_id=form_config.tenant_id
        ).first()
        if potential_owner:
            lead.owner = potential_owner
            lead.save(update_fields=['owner'])
    
    # Update form stats
    form_config.form_submissions += 1
    if lead.status == 'converted':
        form_config.conversion_rate = (form_config.conversion_rate * (form_config.form_submissions - 1) + 100) / form_config.form_submissions
    else:
        form_config.conversion_rate = (form_config.conversion_rate * (form_config.form_submissions - 1)) / form_config.form_submissions
    form_config.save(update_fields=['form_submissions', 'conversion_rate'])
    
    return lead

def find_duplicate_accounts(lead_data, tenant_id):
    """Find existing accounts that match lead data."""
    duplicates = Account.objects.filter(tenant_id=tenant_id)
    
    # Match by company name
    if lead_data.get('company'):
        duplicates = duplicates.filter(name__icontains=lead_data['company'])
    
    # Match by email (through contacts)
    if lead_data.get('email'):
        duplicates = duplicates.filter(
            contacts__email__iexact=lead_data['email']
        )
    
    return duplicates.distinct()