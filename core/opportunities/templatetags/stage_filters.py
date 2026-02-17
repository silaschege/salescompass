from django import template

register = template.Library()

@register.filter
def stage_color(stage_code):
    """
    Convert opportunity stage code to Bootstrap color class.
    
    Usage: {{ stage_code|stage_color }}
    """
    color_map = {
        'prospecting': 'secondary',
        'qualification': 'info',
        'proposal': 'warning', 
        'negotiation': 'primary',
        'closed_won': 'success',
        'closed_lost': 'danger',
    }
    return color_map.get(stage_code, 'secondary')