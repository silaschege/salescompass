from django.db import models
from django.db.models import Q

class VisibilityAwareManager(models.Manager):
    """
    Manager that filters querysets based on the user's visibility permissions.
    Usage: Model.objects.for_user(user)
    """
    
    def for_user(self, user):
        """
        Return a queryset filtered by the user's visibility rules.
        """
        # Superusers see everything
        if user.is_superuser:
            return self.get_queryset()
            
        # Get the visibility rule for this model from the user's role
        # Assuming user.role.data_visibility_rules is a dict like {'leads': 'team_only'}
        model_name = self.model._meta.model_name
        # Default to 'own_only' if not specified
        visibility = 'own_only'
        
        if user.role and user.role.data_visibility_rules:
            visibility = user.role.data_visibility_rules.get(model_name, 'own_only')
            
        # Handle 'all' visibility (e.g. admin role for specific module)
        if visibility == 'all':
            return self.get_queryset()
            
        # Base queryset
        qs = self.get_queryset()
        
        if visibility == 'own_only':
            return qs.filter(owner=user)
            
        elif visibility == 'territory_only':
            # Filter by records owned by users in the same territory
            if hasattr(user, 'team_member') and user.team_member.territory:
                return qs.filter(
                    owner__team_member__territory=user.team_member.territory
                )
            else:
                # Fallback to own only if user has no territory
                return qs.filter(owner=user)
                
        elif visibility == 'team_only':
            # Filter by records owned by user OR their direct reports
            # This assumes a hierarchical team structure via TeamMember.manager
            if hasattr(user, 'team_member'):
                # Get users who report to this user
                # We need to import TeamMember dynamically to avoid circular imports if possible,
                # but since TeamMember depends on User, and Manager is in Core, we might need to use string references or helper
                # For now, let's rely on the related_name 'reports' from TeamMember model:
                # user.team_member.reports.all() gives TeamMembers who report to this user.
                
                # Get IDs of user and their reports
                team_user_ids = [user.id]
                
                # Add direct reports
                reports = user.team_member.reports.all().values_list('user_id', flat=True)
                team_user_ids.extend(reports)
                
                return qs.filter(owner__id__in=team_user_ids)
            else:
                return qs.filter(owner=user)
                
        # Default fallback
        return qs.filter(owner=user)