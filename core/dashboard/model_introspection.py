"""
Model Introspection Utilities
Provides functions to discover available models and their fields for dynamic widget configuration.
"""
from django.apps import apps
from django.db import models
from django.db.models import fields
from typing import List, Dict, Any, Optional


# Widget-to-Model mapping for auto-selection
WIDGET_MODEL_MAPPING = {
    'tasks': 'tasks',
    'leads': 'leads',
    'opportunities': 'opportunities',
    'accounts': 'accounts',
    'cases': 'cases',
    'sales': 'sales',
    'products': 'products',
    'proposals': 'proposals',
    'marketing': 'marketing',
    'nps': 'nps',
    'engagement': 'engagement',
    'communication': 'communication',
    'commissions': 'sales',
    'reports': 'reports',
    'billing': 'billing',
}



def get_available_models() -> List[Dict[str, str]]:
    """
    Get list of available models for dashboard widgets using dynamic discovery.
    
    Returns:
        List of dicts with model information: {id, name, app_label, model_name}
    """
    available = []
    
    # Internal apps to include (or external apps if needed)
    # We filter out Django system apps and administrative apps
    EXCLUDED_APPS = [
        'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles', 
        'axes', 'reversion', 'django_extensions', 'rest_framework'
    ]
    
    for app_config in apps.get_app_configs():
        if app_config.label in EXCLUDED_APPS:
            continue
            
        for model in app_config.get_models():
            # Skip ManyToMany intermediary models
            if model._meta.auto_created:
                continue
                
            model_id = f"{app_config.label}.{model._meta.model_name}"
            
            available.append({
                'id': model_id,
                'name': model._meta.verbose_name_plural.title(),
                'app_label': app_config.label,
                'model_name': model._meta.model_name,
                'model_path': model_id,
            })
            
    # Sort by name
    return sorted(available, key=lambda x: x['name'])




def get_model_class(model_id: str) -> Optional[Any]:
    """
    Get Django model class from model ID.
    
    Args:
        model_id: Model identifier (e.g., 'leads.lead', 'accounts.account')
    
    Returns:
        Django model class or None if not found
    """
    try:
        # Expected format: app_label.model_name
        if '.' not in model_id:
            # Try legacy lookup for backward compatibility if needed, or fail
            # For now, let's assume we strictly follow app_label.model_name
            return None
            
        app_label, model_name = model_id.split('.')
        return apps.get_model(app_label, model_name)
    except (LookupError, ValueError):
        return None



def get_field_type(field) -> str:
    """
    Determine the type of a Django model field.
    
    Args:
        field: Django model field instance
    
    Returns:
        Field type string (e.g., 'char', 'integer', 'boolean', 'foreign_key')
    """
    if isinstance(field, models.BooleanField):
        return 'boolean'
    elif isinstance(field, models.IntegerField):
        return 'integer'
    elif isinstance(field, models.DecimalField):
        return 'decimal'
    elif isinstance(field, models.FloatField):
        return 'float'
    elif isinstance(field, models.DateField):
        return 'date'
    elif isinstance(field, models.DateTimeField):
        return 'datetime'
    elif isinstance(field, models.EmailField):
        return 'email'
    elif isinstance(field, models.ForeignKey):
        return 'foreign_key'
    elif isinstance(field, models.ManyToManyField):
        return 'many_to_many'
    elif isinstance(field, models.CharField):
        return 'char'
    elif isinstance(field, models.TextField):
        return 'text'
    else:
        return 'unknown'


def is_filterable_field(field) -> bool:
    """
    Check if a field can be used for filtering.
    
    Args:
        field: Django model field instance
    
    Returns:
        True if field is filterable, False otherwise
    """
    # Exclude auto-generated fields and complex relationships
    if field.auto_created:
        return False
    
    if isinstance(field, (models.ManyToManyField, models.FileField, models.ImageField)):
        return False
    
    # Exclude JSON fields for now (complex filtering)
    if isinstance(field, models.JSONField):
        return False
    
    return True


def is_aggregatable_field(field) -> bool:
    """
    Check if a field supports aggregation operations (sum, avg, min, max).
    
    Args:
        field: Django model field instance
    
    Returns:
        True if field is aggregatable, False otherwise
    """
    # Only numeric and date fields support aggregation
    return isinstance(field, (
        models.IntegerField,
        models.DecimalField,
        models.FloatField,
        models.DateField,
        models.DateTimeField,
    ))


def get_model_fields(model_id: str) -> List[Dict[str, Any]]:
    """
    Get field information for a given model.
    
    Args:
        model_id: Model identifier (e.g., 'tasks', 'leads')
    
    Returns:
        List of dicts with field information: {name, type, verbose_name, choices, filterable, aggregatable}
    """
    model_class = get_model_class(model_id)
    if not model_class:
        return []
    
    fields = []
    
    for field in model_class._meta.get_fields():
        # Skip reverse relations
        if field.auto_created and not field.concrete:
            continue
        
        field_type = get_field_type(field)
        
        # Get choices if available
        choices = []
        if hasattr(field, 'choices') and field.choices:
            choices = [{'value': value, 'label': label} for value, label in field.choices]
        
        # For ForeignKey fields, get related model info
        related_model = None
        if isinstance(field, models.ForeignKey):
            related_model = {
                'app_label': field.related_model._meta.app_label,
                'model_name': field.related_model._meta.model_name,
                'verbose_name': field.related_model._meta.verbose_name,
            }
        
        fields.append({
            'name': field.name,
            'type': field_type,
            'verbose_name': field.verbose_name if hasattr(field, 'verbose_name') else field.name,
            'choices': choices,
            'filterable': is_filterable_field(field),
            'aggregatable': is_aggregatable_field(field),
            'related_model': related_model,
            'null': field.null if hasattr(field, 'null') else False,
            'blank': field.blank if hasattr(field, 'blank') else False,
        })
    
    return fields


def get_filter_operators(field_type: str) -> List[Dict[str, str]]:
    """
    Get available filter operators for a given field type.
    
    Args:
        field_type: Field type string (e.g., 'char', 'integer', 'boolean')
    
    Returns:
        List of dicts with operator information: {value, label}
    """
    # Common operators for all types
    common = [
        {'value': 'exact', 'label': 'Equals'},
        {'value': 'isnull', 'label': 'Is Null'},
    ]
    
    if field_type in ['char', 'text', 'email']:
        return common + [
            {'value': 'icontains', 'label': 'Contains'},
            {'value': 'istartswith', 'label': 'Starts With'},
            {'value': 'iendswith', 'label': 'Ends With'},
        ]
    
    elif field_type in ['integer', 'decimal', 'float']:
        return common + [
            {'value': 'gt', 'label': 'Greater Than'},
            {'value': 'gte', 'label': 'Greater Than or Equal'},
            {'value': 'lt', 'label': 'Less Than'},
            {'value': 'lte', 'label': 'Less Than or Equal'},
        ]
    
    elif field_type in ['date', 'datetime']:
        return common + [
            {'value': 'gt', 'label': 'After'},
            {'value': 'gte', 'label': 'On or After'},
            {'value': 'lt', 'label': 'Before'},
            {'value': 'lte', 'label': 'On or Before'},
        ]
    
    elif field_type == 'boolean':
        return [
            {'value': 'exact', 'label': 'Equals'},
        ]
    
    elif field_type == 'foreign_key':
        return [
            {'value': 'exact', 'label': 'Equals'},
            {'value': 'isnull', 'label': 'Is Null'},
        ]
    
    return common


def get_aggregation_types() -> List[Dict[str, str]]:
    """
    Get available aggregation types.
    
    Returns:
        List of dicts with aggregation information: {value, label, requires_field}
    """
    return [
        {'value': 'count', 'label': 'Count (Total Records)', 'requires_field': False},
        {'value': 'sum', 'label': 'Sum (Total Value)', 'requires_field': True},
        {'value': 'avg', 'label': 'Average', 'requires_field': True},
        {'value': 'min', 'label': 'Minimum', 'requires_field': True},
        {'value': 'max', 'label': 'Maximum', 'requires_field': True},
    ]


def get_default_model_for_widget(widget_type: str) -> str:
    """
    Get the default model for a given widget type.
    
    Args:
        widget_type: Widget type identifier (e.g., "tasks", "leads")
    
    Returns:
        Model ID string or empty string if no mapping exists
    """
    return WIDGET_MODEL_MAPPING.get(widget_type, "")

