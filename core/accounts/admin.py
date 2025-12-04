from django.contrib import admin
from .models import Account, Contact

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'tier', 'health_score', 'esg_engagement', 'status','owner']
    list_filter = ['industry', 'tier', 'esg_engagement', 'status']
    search_fields = ['name', 'contacts__email']
    readonly_fields = ['health_score', 'clv']

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'account', 'email']
    list_filter = ['account__industry']