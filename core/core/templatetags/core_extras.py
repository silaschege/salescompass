from django import template
import json
 
register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='dict_to_json')
def dict_to_json(value):
    """Convert a dict or JSON field to a formatted JSON string."""
    try:
        if isinstance(value, str):
            return value
        return json.dumps(value, indent=2)
    except (ValueError, TypeError):
        return str(value)
