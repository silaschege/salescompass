"""
Central registry of available applications for the App Permissons system.
Used to populate the App Settings page and validate permissions.
"""

AVAILABLE_APPS = [
    # Customer
    {
        'id': 'reachout',
        'name': 'Reachout',
        'icon': 'bi-people',
        'url_name': 'leads:lead_list',
        'category': 'customer',
        'description': 'Manage leads and outreach'
    },
    {
        'id': 'accounts',
        'name': 'Accounts', 
        'icon': 'bi-briefcase',
        'url_name': 'accounts:accounts_list',
        'category': 'customer',
        'description': 'Manage customer accounts'
    },
    
    # Work
    {
        'id': 'register_customer',
        'name': 'Register Customer',
        'icon': 'bi-person-plus',
        'url_name': 'accounts:accounts_create',
        'category': 'work',
        'description': 'Onboard new customers'
    },
    {
        'id': 'sale', # Placeholder based on previous view logic
        'name': 'Sale',
        'icon': 'bi-cart',
        'url_name': 'leads:lead_pipeline',
        'category': 'work',
        'description': 'Sales pipeline'
    },
    
    # Analytics
    {
        'id': 'reports',
        'name': 'Reports',
        'icon': 'bi-bar-chart',
        'url_name': 'reports:list',
        'category': 'analytics',
        'description': 'View reports and analytics'
    },
    
    # Admin
    {
        'id': 'settings',
        'name': 'Settings',
        'icon': 'bi-gear',
        'url_name': 'settings:home',
        'category': 'admin',
        'description': 'Application settings'
    },
    
    # Control Plane (Superuser Only - typically not toggleable but listed for completeness if needed)
    {
        'id': 'tenants',
        'name': 'Tenants',
        'icon': 'bi-building',
        'url_name': 'tenants:list',
        'category': 'control',
        'description': 'Manage tenants'
    },
    {
        'id': 'billing',
        'name': 'Billing',
        'icon': 'bi-credit-card',
        'url_name': 'tenants:revenue_analytics',
        'category': 'control',
        'description': 'Billing and revenue'
    },
    {
        'id': 'control_register_customer',
        'name': 'Register Customer (Control)',
        'icon': 'bi-person-plus',
        'url_name': 'tenants:create',
        'category': 'control',
        'description': 'Register new tenant customer'
    },
    {
        'id': 'users',
        'name': 'Users',
        'icon': 'bi-people-fill',
        'url_name': 'users:list',
        'category': 'control',
        'description': 'Manage users'
    },
    {
        'id':'audit_logs',
        'name': 'Audit Logs',
        'icon': 'bi-journal-text',
        'url_name': 'audit_logs:list',
        'category': 'control',
        'description': 'View audit logs'
        
    }
]

def get_app_by_id(app_id):
    for app in AVAILABLE_APPS:
        if app['id'] == app_id:
            return app
    return None
