"""
Query Builder Utility
Constructs Django ORM queries from widget configuration
for dynamic data retrieval in dashboard widgets.
"""
from django.db.models import Count, Sum, Avg, Min, Max, Q
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from .model_introspection import get_model_class


class QueryBuilderError(Exception):
    """Custom exception for query builder errors"""
    pass


def validate_configuration(config: Dict[str, Any]) -> bool:
    """
    Validate widget configuration before building query.
    
    Args:
        config: Widget configuration dict
    
    Returns:
        True if valid, raises QueryBuilderError if invalid
    """
    if not config.get('model'):
        raise QueryBuilderError("Model is required")
    
    if config.get('aggregation') in ['sum', 'avg', 'min', 'max']:
        if not config.get('aggregation_field'):
            raise QueryBuilderError(f"{config['aggregation']} aggregation requires a field")
    
    return True


def build_queryset(model_id: str, filters: Optional[List[Dict[str, Any]]] = None, 
                   time_range: Optional[int] = None, tenant_id: Optional[str] = None):
    """
    Build a Django queryset from configuration.
    
    Args:
        model_id: Model identifier (e.g., 'tasks', 'leads')
        filters: List of filter dicts: [{field, operator, value}]
        time_range: Number of days to include (filters by created_at/updated_at)
        tenant_id: Tenant ID for multi-tenant filtering
    
    Returns:
        Django queryset
    """
    model_class = get_model_class(model_id)
    if not model_class:
        raise QueryBuilderError(f"Model '{model_id}' not found")
    
    # Start with base queryset
    queryset = model_class.objects.all()
    
    # Apply tenant filtering if model has tenant_id field
    if tenant_id and hasattr(model_class, 'tenant_id'):
        queryset = queryset.filter(tenant_id=tenant_id)
    
    # Apply time range filter
    if time_range:
        cutoff_date = timezone.now() - timedelta(days=time_range)
        
        # Try to filter by created_at, fall back to updated_at
        if hasattr(model_class, 'created_at'):
            queryset = queryset.filter(created_at__gte=cutoff_date)
        elif hasattr(model_class, 'updated_at'):
            queryset = queryset.filter(updated_at__gte=cutoff_date)
    
    # Apply custom filters
    if filters:
        queryset = apply_filters(queryset, filters)
    
    return queryset


def apply_filters(queryset, filters: List[Dict[str, Any]]):
    """
    Apply filter criteria to a queryset.
    
    Args:
        queryset: Django queryset
        filters: List of filter dicts: [{field, operator, value}]
    
    Returns:
        Filtered queryset
    """
    for filter_config in filters:
        field = filter_config.get('field')
        operator = filter_config.get('operator', 'exact')
        value = filter_config.get('value')
        
        if not field:
            continue
        
        # Build filter lookup
        if operator == 'isnull':
            # Special case: isnull expects boolean value
            lookup = {f"{field}__isnull": value in [True, 'true', '1', 1]}
        else:
            lookup = {f"{field}__{operator}": value}
        
        try:
            queryset = queryset.filter(**lookup)
        except Exception as e:
            # Log error but don't fail the entire query
            print(f"Filter error: {e}")
            continue
    
    return queryset


def apply_aggregation(queryset, aggregation_type: str, 
                      aggregation_field: Optional[str] = None) -> Any:
    """
    Apply aggregation to a queryset.
    
    Args:
        queryset: Django queryset
        aggregation_type: Type of aggregation (count, sum, avg, min, max)
        aggregation_field: Field to aggregate (required for sum/avg/min/max)
    
    Returns:
        Aggregation result (number)
    """
    if aggregation_type == 'count':
        return queryset.count()
    
    elif aggregation_type == 'sum':
        if not aggregation_field:
            raise QueryBuilderError("Sum aggregation requires a field")
        result = queryset.aggregate(total=Sum(aggregation_field))
        return result['total'] or 0
    
    elif aggregation_type == 'avg':
        if not aggregation_field:
            raise QueryBuilderError("Average aggregation requires a field")
        result = queryset.aggregate(average=Avg(aggregation_field))
        return result['average'] or 0
    
    elif aggregation_type == 'min':
        if not aggregation_field:
            raise QueryBuilderError("Min aggregation requires a field")
        result = queryset.aggregate(minimum=Min(aggregation_field))
        return result['minimum'] or 0
    
    elif aggregation_type == 'max':
        if not aggregation_field:
            raise QueryBuilderError("Max aggregation requires a field")
        result = queryset.aggregate(maximum=Max(aggregation_field))
        return result['maximum'] or 0
    
    else:
        raise QueryBuilderError(f"Unknown aggregation type: {aggregation_type}")


def execute_widget_query(config: Dict[str, Any], tenant_id: Optional[str] = None) -> Any:
    """
    Execute a complete widget query from configuration.
    
    Args:
        config: Widget configuration dict with keys:
            - model: Model identifier
            - filters: List of filter dicts (optional)
            - aggregation: Aggregation type (optional, defaults to 'count')
            - aggregation_field: Field for aggregation (optional)
            - time_range: Days to include (optional)
        tenant_id: Tenant ID for filtering
    
    Returns:
        Query result (typically a number for aggregations)
    """
    # Validate configuration
    validate_configuration(config)
    
    # Build queryset
    queryset = build_queryset(
        model_id=config['model'],
        filters=config.get('filters', []),
        time_range=config.get('time_range'),
        tenant_id=tenant_id
    )
    
    # Apply aggregation
    aggregation_type = config.get('aggregation', 'count')
    aggregation_field = config.get('aggregation_field')
    
    result = apply_aggregation(queryset, aggregation_type, aggregation_field)
    
    return result


def get_widget_data(config: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get formatted widget data from configuration.
    
    Args:
        config: Widget configuration dict
        tenant_id: Tenant ID for filtering
    
    Returns:
        Dict with widget data: {value, label, model, filters_applied}
    """
    try:
        value = execute_widget_query(config, tenant_id)
        
        # Build descriptive label
        model_name = config.get('model', 'Unknown')
        aggregation = config.get('aggregation', 'count')
        
        if aggregation == 'count':
            label = f"Total {model_name.title()}"
        else:
            field = config.get('aggregation_field', 'value')
            label = f"{aggregation.title()} of {field}"
        
        return {
            'value': value,
            'label': label,
            'model': model_name,
            'filters_applied': len(config.get('filters', [])),
            'success': True,
        }
    
    except Exception as e:
        return {
            'value': 0,
            'label': 'Error',
            'error': str(e),
            'success': False,
        }
