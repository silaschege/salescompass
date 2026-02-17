from django import template
from django.contrib.contenttypes.models import ContentType
from tasks.models import Task

register = template.Library()

@register.inclusion_tag('tasks/partials/generic_task_list.html', takes_context=True)
def render_object_tasks(context, obj):
    """
    Renders a task list for any given object.
    Usage: {% render_object_tasks object_instance %}
    """
    if not obj:
        return {'tasks': []}
        
    request = context.get('request')
    tenant_id = getattr(request.user, 'tenant_id', None) if request and request.user.is_authenticated else None
    
    content_type = ContentType.objects.get_for_model(obj)
    
    # Fetch tasks linked to this object via Generic Relations
    tasks = Task.objects.filter(
        content_type=content_type,
        object_id=obj.id
    )
    
    if tenant_id:
        tasks = tasks.filter(tenant_id=tenant_id)
        
    return {
        'tasks': tasks,
        'related_object': obj,
        'content_type_id': content_type.id,
        'object_id': obj.id, 
        'request': request
    }

@register.simple_tag
def get_object_task_count(obj):
    """
    Returns the count of tasks for a given object.
    Usage: {% get_object_task_count object_instance %}
    """
    if not obj:
        return 0
        
    content_type = ContentType.objects.get_for_model(obj)
    return Task.objects.filter(
        content_type=content_type,
        object_id=obj.id
    ).count()
