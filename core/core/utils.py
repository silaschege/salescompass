"""
Core utilities for the SalesCompass platform.
"""
from django.db.models import QuerySet

def get_queryset_for_user(user, model) -> QuerySet:
    """
    Returns a queryset filtered by tenant and user role/level.
    
    Logic:
    1. Filter by tenant_id (direct or via account).
    2. If user is Admin or Manager (based on Role), return all tenant records.
    3. If user is a regular User (or other roles), return only records owned by them (owner=user).
    """
    if not user.is_authenticated:
        return model.objects.none()

    queryset = model.objects.all()

    # 1. Filter by tenant
    # Check if model has tenant_id field
    has_tenant_id = False
    try:
        model._meta.get_field('tenant_id')
        has_tenant_id = True
    except:
        pass

    if has_tenant_id:
        queryset = queryset.filter(tenant_id=user.tenant_id)
    else:
        # Try filtering via account relationship
        try:
            model._meta.get_field('account')
            queryset = queryset.filter(account__tenant_id=user.tenant_id)
        except:
            # No tenant context found; assume global or handled otherwise
            pass

    # Check for superuser
    if user.is_superuser:
        return model.objects.all() # Superuser sees all tenants

    # Role-based filtering
    if user.role:
        role_name = user.role.name.lower()
        if 'admin' in role_name or 'manager' in role_name:
            return queryset
    
    # Default: Filter by owner if the model has an 'owner' field
    if hasattr(model, 'owner'):
        return queryset.filter(owner=user)
    
    return queryset

def anonymize_user_data(user_id: int) -> None:
    """
    GDPR-compliant data anonymization on user offboarding.
    Replaces PII with placeholders; keeps analytics intact.
    """
    from django.db import transaction
    from core.models import User
    from accounts.models import Account, Contact
    from leads.models import Lead

    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id)
        
        # Anonymize user
        user.email = f"anon-{user.id}@example.com"
        user.username = f"[ANONYMIZED-{user.id}]"
        user.first_name = "[REDACTED]"
        user.last_name = "[REDACTED]"
        user.phone = ""
        user.save()

        # Anonymize accounts
        Account.objects.filter(owner=user).update(
            name=f"[ANONYMIZED-{user.id}]",
            website="",
            address="",
            gdpr_consent=False,
            ccpa_consent=False
        )

        # Anonymize contacts
        Contact.objects.filter(account__owner=user).update(
            first_name="[REDACTED]",
            last_name="[REDACTED]",
            email=f"anon-{user.id}@example.com",
            phone=""
        )

        # Anonymize leads
        Lead.objects.filter(owner=user).update(
            first_name="[REDACTED]",
            last_name="[REDACTED]",
            email=f"lead-anon-{user.id}@example.com",
            phone=""
        )


def check_consent(account) -> dict:
    """
    Check current consent status for compliance reporting.
    """
    return {
        'gdpr': account.gdpr_consent,
        'ccpa': account.ccpa_consent,
        'csrd': getattr(account, 'esg_score', None) and account.esg_score.csr_ready
    }