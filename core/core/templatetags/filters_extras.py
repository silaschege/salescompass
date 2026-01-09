from django import template
import os
import json

register = template.Library()

@register.filter
def status_count(cases, status):
    """Return count of cases with given status."""
    return len([c for c in cases if c.status == status])

@register.filter
def status_color(status):
    """Return Bootstrap color class for status."""
    colors = {
        'new': 'secondary',
        'in_progress': 'warning', 
        'resolved': 'primary',
        'closed': 'success'
    }
    return colors.get(status, 'secondary')

@register.filter  
def status_color_text(status):
    """Return Bootstrap text color class for status."""
    colors = {
        'new': 'secondary',
        'in_progress': 'warning',
        'resolved': 'primary', 
        'closed': 'success'
    }
    return colors.get(status, 'secondary')

@register.filter
def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000'.
    """
    if value is None:
        return '0'
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value
    
@register.filter
def to_string(value):
    """Convert value to string."""
    return str(value)
    
@register.filter
def get(dictionary, key):
    """Get item from nested dictionary in templates."""
    if dictionary is None:
        return {}
    return dictionary.get(key, {})

@register.filter
def make_list(value):
    """Convert a string of digits to a list for iteration."""
    if isinstance(value, str):
        return list(value)
    return value

@register.filter
def basename(value):
    """
    Return the basename of a file path.
    
    Usage: {{ file_field.name|basename }}
    Example: "documents/report.pdf" -> "report.pdf"
    """
    if not value:
        return ""
    return os.path.basename(str(value))

@register.filter
def pprint(value):
    """Pretty print JSON/dict objects in templates."""
    if isinstance(value, dict):
        return json.dumps(value, indent=2, default=str)
    return str(value)

@register.filter
def get_item(value, arg):
    """
    Get an item from a list/dict by index/key.
    
    Usage: {{ list|get_item:0 }} or {{ dict|get_item:"key_name" }}
    """
    try:
        if isinstance(value, dict):
            return value.get(arg)
        elif isinstance(value, (list, tuple)):
            return value[int(arg)]
        else:
            return ''
    except (KeyError, IndexError, ValueError, TypeError):
        return ''