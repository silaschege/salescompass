from django.contrib import admin
from .models import Account, AccountTeamMember, Contact, Role, AccountsUserProfile

class AccountTeamMemberInline(admin.TabularInline):
    model = AccountTeamMember
    extra = 1

class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'industry', 'status', 'tier', 'owner', 'created_at', 'annual_revenue')
    list_filter = ('industry', 'status', 'tier', 'esg_engagement', 'owner')
    search_fields = ('account_name', 'website', 'phone')
    inlines = [AccountTeamMemberInline, ContactInline]
    fieldsets = (
        (None, {
            'fields': ('account_name', 'parent', 'owner', 'description', 'tags')
        }),
        ('Contact Info', {
            'fields': ('website', 'phone', 'linkedin_url', 'twitter_url', 'facebook_url')
        }),
        ('Address', {
            'fields': ('billing_address_line1', 'billing_address_line2', 'billing_city', 'billing_state', 'billing_postal_code', 'country')
        }),
        ('Classification', {
            'fields': ('industry', 'status', 'tier', 'esg_engagement')
        }),
        ('Business Details', {
            'fields': ('annual_revenue', 'number_of_employees', 'last_activity_at')
        }),
        ('Metrics', {
            'fields': ('health_score', 'partners', 'competitors')
        }),
        ('Compliance', {
            'fields': ('gdpr_consent', 'ccpa_consent')
        }),
    )

@admin.register(AccountsUserProfile)
class AccountsUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('favorite_accounts',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'tenant', 'is_system_role']
    list_filter = ['tenant', 'is_system_role', 'is_assignable']
    search_fields = ['name', 'description']
