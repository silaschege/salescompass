from django import template

register = template.Library()

@register.filter
def div_float(value, arg):
    """Division filter for templates."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def get(dictionary, key):
    """Get item from dictionary in templates."""
    return dictionary.get(key)



@register.filter
def sub(value, arg):
    """Subtraction filter for templates."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div_int(value, arg):
    """Division filter for templates."""
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter(name='abs')
def absolute_value(value):
    """Return absolute value of number."""
    try:
        import builtins
        return builtins.abs(float(value))
    except (ValueError, TypeError):
        return value


@register.filter
def div(value, arg):
    """Division filter for templates."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplication filter for templates."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    


@register.filter
def count_enabled(queryset):
    """
    Counts items where enabled is True.
    Works for Lists and QuerySets.
    """
    if hasattr(queryset, 'filter'):
        # Efficient DB count for QuerySets
        return queryset.filter(enabled=True).count()
    # List comprehension for standard lists
    return len([item for item in queryset if getattr(item, 'enabled', False)])


