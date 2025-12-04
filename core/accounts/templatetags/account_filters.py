from django import template

register = template.Library()

@register.filter
def active_count(accounts):
    """Return count of accounts with status 'active'."""
    return len([a for a in accounts if a.status == 'active'])

@register.filter
def at_risk_count(accounts):
    """Return count of accounts with status 'at_risk'."""
    return len([a for a in accounts if a.status == 'at_risk'])

@register.filter
def churned_count(accounts):
    """Return count of accounts with status 'churned'."""
    return len([a for a in accounts if a.status == 'churned'])

@register.filter
def status_count(accounts, status):
    """Return count of accounts with given status."""
    return len([a for a in accounts if a.status == status])

