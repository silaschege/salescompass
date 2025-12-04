from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'permission_count']
    readonly_fields = ['permission_count']

    def permission_count(self, obj):
        return len(obj.permissions)
    permission_count.short_description = 'Permissions'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Permissions', {'fields': ('role', 'phone', 'mfa_enabled')}),
    )
    list_display = ['email', 'username', 'role', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username']