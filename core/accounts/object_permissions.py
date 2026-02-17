from core.object_permissions import ObjectPermissionPolicy
from core.models import User
from django.db import models

class AccountObjectPolicy(ObjectPermissionPolicy):
    @classmethod
    def can_view(cls, user: User, obj: Any) -> bool:
        if user.is_superuser:
            return True
        if user.has_perm('accounts:*'):
            return True
        if obj.owner == user:
            return True
        return False

    @classmethod
    def get_viewable_queryset(cls, user: User, queryset: models.QuerySet) -> models.QuerySet:
        if user.is_superuser or user.has_perm('accounts:*'):
            return queryset
        return queryset.filter(owner=user)