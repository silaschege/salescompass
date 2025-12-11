from django.apps import apps
from django.db import models
from django.db.models import Q


def get_queryset_for_user(user, model_class):
    """
    Get a queryset filtered by the user's permissions and visibility rules.
    
    Args:
        user: The user object
        model_class: The model class to filter
    
    Returns:
        Filtered queryset based on user permissions
    """
    # Default to all objects for superusers
    if user.is_superuser:
        return model_class.objects.all()
    
    # For regular users, apply visibility rules based on their role
    # This is a simplified implementation - in a real application, 
    # you would have more sophisticated permission logic
    
    # For example, users might only see records they own
    if hasattr(model_class, 'owner'):
        return model_class.objects.filter(
            Q(owner=user) | Q(owner__team_member__manager=user)
        )
    elif hasattr(model_class, 'user'):
        # If the model has a user field that represents ownership
        return model_class.objects.filter(user=user)
    elif hasattr(model_class, 'created_by'):
        # If the model has a created_by field
        return model_class.objects.filter(created_by=user)
    else:
        # If no ownership field exists, apply tenant isolation if available
        if hasattr(model_class, 'tenant_id'):
            return model_class.objects.filter(tenant_id=user.tenant_id)
        else:
            # Return all records for the user's tenant if the model supports it
            return model_class.objects.all()


def get_dynamic_choice_value(instance, old_field_name, new_field_name, fallback_display_field='name'):
    """
    Get the value from a dynamic choice field, with fallback to the old field.
    
    Args:
        instance: The model instance
        old_field_name: Name of the old hardcoded choice field
        new_field_name: Name of the new dynamic choice reference field
        fallback_display_field: Field to use for display value if new field is populated
    
    Returns:
        The value from the new field if populated, otherwise from the old field
    """
    new_field_value = getattr(instance, new_field_name, None)
    old_field_value = getattr(instance, old_field_name, None)
    
    if new_field_value:
        # If the new dynamic choice field is populated, return its display value
        return getattr(new_field_value, fallback_display_field, str(new_field_value))
    else:
        # Otherwise, return the old field value
        return old_field_value


def get_dynamic_choice_id(instance, old_field_name, new_field_name):
    """
    Get the ID from a dynamic choice field, with fallback to the old field.
    
    Args:
        instance: The model instance
        old_field_name: Name of the old hardcoded choice field
        new_field_name: Name of the new dynamic choice reference field
    
    Returns:
        The ID from the new field if populated, otherwise the old field value
    """
    new_field_value = getattr(instance, new_field_name, None)
    old_field_value = getattr(instance, old_field_name, None)
    
    if new_field_value:
        # If the new dynamic choice field is populated, return its ID
        return new_field_value.id
    else:
        # Otherwise, return the old field value
        return old_field_value


def get_dynamic_choice_object(instance, new_field_name, choice_model_name, tenant_id):
    """
    Get the dynamic choice object, creating it from the old field value if needed.
    
    Args:
        instance: The model instance
        new_field_name: Name of the new dynamic choice reference field
        choice_model_name: Name of the dynamic choice model (e.g., 'SystemConfigType')
        tenant_id: Tenant ID for the dynamic choice
    
    Returns:
        The dynamic choice object
    """
    new_field_value = getattr(instance, new_field_name, None)
    
    if new_field_value:
        # If the new field is already populated, return it
        return new_field_value
    else:
        # Otherwise, we need to create or get the dynamic choice based on the old field
        choice_model = apps.get_model('core', choice_model_name)
        
        # Get the old field name by removing '_ref' suffix from new field name
        old_field_name = new_field_name.replace('_ref', '')
        old_field_value = getattr(instance, old_field_name, None)
        
        if old_field_value:
            # Try to get or create the dynamic choice object
            choice_obj, created = choice_model.objects.get_or_create(
                name=old_field_value,
                tenant_id=tenant_id,
                defaults={
                    'display_name': old_field_value.title().replace('_', ' '),
                    'is_active': True
                }
            )
            return choice_obj
    
    return None


def migrate_to_dynamic_choices(model_class, old_field_name, new_field_name, choice_model_name, user=None):
    """
    Migrate existing records from old hardcoded choices to new dynamic choices.
    
    Args:
        model_class: The model class to migrate
        old_field_name: Name of the old hardcoded choice field
        new_field_name: Name of the new dynamic choice reference field
        choice_model_name: Name of the dynamic choice model
        user: User performing the migration (for audit purposes)
    """
    choice_model = apps.get_model('core', choice_model_name)
    updated_count = 0
    
    for instance in model_class.objects.all():
        # Skip if new field is already populated
        if getattr(instance, new_field_name, None):
            continue
            
        old_field_value = getattr(instance, old_field_name, None)
        
        if old_field_value:
            # Find or create the corresponding dynamic choice
            tenant_id = getattr(instance, 'tenant_id', None)
            if tenant_id:
                choice_obj, created = choice_model.objects.get_or_create(
                    name=old_field_value,
                    tenant_id=tenant_id,
                    defaults={
                        'display_name': old_field_value.title().replace('_', ' '),
                        'is_active': True
                    }
                )
                
                # Set the new field to reference the dynamic choice
                setattr(instance, new_field_name, choice_obj)
                
                # Save the instance
                instance.save()
                updated_count += 1
                
                # Add audit trail if available
                if hasattr(instance, '_current_user') or user:
                    current_user = getattr(instance, '_current_user', user)
                    # Add audit logging here if needed
    
    return updated_count


def get_dynamic_choices_for_model(model_name, tenant_id):
    """
    Get all dynamic choices for a specific model and tenant.
    
    Args:
        model_name: Name of the dynamic choice model
        tenant_id: Tenant ID
    
    Returns:
        QuerySet of dynamic choice objects
    """
    try:
        model_class = apps.get_model('core', model_name)
        return model_class.objects.filter(tenant_id=tenant_id, is_active=True).order_by('name')
    except LookupError:
        # Model doesn't exist
        return None


def create_dynamic_choice(model_name, tenant_id, name, display_name=None, **kwargs):
    """
    Create a new dynamic choice with proper tenant isolation.
    
    Args:
        model_name: Name of the dynamic choice model
        tenant_id: Tenant ID
        name: Name of the choice
        display_name: Display name (defaults to titleized name if not provided)
        **kwargs: Additional fields to set on the choice
    
    Returns:
        Created dynamic choice object
    """
    if not display_name:
        display_name = name.title().replace('_', ' ')
    
    model_class = apps.get_model('core', model_name)
    
    choice = model_class(
        name=name,
        display_name=display_name,
        tenant_id=tenant_id,
        **kwargs
    )
    choice.save()
    
    return choice


def update_dynamic_choice_references(model_class, old_value, new_choice, tenant_id):
    """
    Update all references from an old choice value to a new choice object.
    
    Args:
        model_class: The model class that has the reference
        old_value: The old hardcoded choice value to replace
        new_choice: The new dynamic choice object
        tenant_id: Tenant ID to scope the updates
    
    Returns:
        Number of records updated
    """
    # Get the reference field name (assuming it ends with '_ref')
    ref_field_name = None
    for field in model_class._meta.get_fields():
        if (isinstance(field, models.ForeignKey) and 
            hasattr(field, 'related_model') and
            field.name.endswith('_ref')):
            if field.related_model == type(new_choice):
                ref_field_name = field.name
                break
    
    if not ref_field_name:
        return 0
    
    # Get the corresponding old field name (without '_ref')
    old_field_name = ref_field_name.replace('_ref', '')
    
    # Update records that have the old value in the old field
    updated_count = 0
    for instance in model_class.objects.filter(tenant_id=tenant_id, **{old_field_name: old_value}):
        setattr(instance, ref_field_name, new_choice)
        instance.save()
        updated_count += 1
    
    return updated_count
