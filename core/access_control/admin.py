from django.contrib import admin
from .models import AccessControl

@admin.register(AccessControl)
class AccessControlAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'access_type', 'scope_type', 'is_enabled', 'tenant', 'role', 'user']
    list_filter = ['access_type', 'scope_type', 'is_enabled', 'tenant']
    search_fields = ['name', 'key']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'key', 'description')
        }),
        ('Access Configuration', {
            'fields': ('access_type', 'scope_type', 'is_enabled', 'rollout_percentage')
        }),
        ('Target', {
            'fields': ('user', 'role', 'tenant')
        }),
        ('Configuration', {
            'fields': ('config_data',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Dynamically adjust fields based on scope_type
        if 'scope_type' in form.base_fields:
            # Note: Checking request.GET or obj might not work perfectly in all cases but works for standard admin
            scope_type = request.GET.get('scope_type')
            if obj and obj.scope_type:
                scope_type = obj.scope_type
            
            if scope_type == 'user':
                form.base_fields['user'].required = True
                form.base_fields['role'].required = False
                form.base_fields['tenant'].required = False
            elif scope_type == 'role':
                form.base_fields['role'].required = True
                form.base_fields['user'].required = False
                form.base_fields['tenant'].required = True # Role is usually within a tenant
            elif scope_type == 'tenant':
                form.base_fields['tenant'].required = True
                form.base_fields['user'].required = False
                form.base_fields['role'].required = False
        
        return form
