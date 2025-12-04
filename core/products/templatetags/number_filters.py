from django import template


register = template.Library()

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
    