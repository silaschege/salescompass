from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def has_perm(user, perm: str) -> bool:
    """
    Usage in templates:
        {% if request.user|has_perm:"accounts:write" %}
            <a href="/accounts/create">Create</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    return user.has_perm(perm)
