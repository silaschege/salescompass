
"""
Central registry of available applications for the App Permissons system.
Used to populate the App Settings page and validate permissions.
"""
# Define which categories are superuser-only
SUPERUSER_ONLY_CATEGORIES = ['control']

AVAILABLE_APPS = [
    # Core Apps
    {
        'id': 'home',
        'name': 'Home',
        'icon': 'bi-house-door',
        'url_name': 'core:home',
        'category': 'core',
        'description': 'SalesCompass Home'
    },
    {
        'id': 'dashboard',
        'name': 'Dashboard',
        'icon': 'bi-speedometer2',
        'url_name': 'dashboard:cockpit',
        'category': 'core',
        'description': 'Main unified dashboard'
    },
    {
        'id': 'accounts',
        'name': 'Accounts',
        'icon': 'bi-briefcase',
        'url_name': 'accounts:account_list',
        'category': 'core',
        'description': 'Manage customer accounts'
    },
    {
        'id': 'tenants',
        'name': 'Tenants',
        'icon': 'bi-building',
        'url_name': 'tenants:tenant_list',
        'category': 'core', # User listed under Core
        'description': 'Manage tenants'
    },
    {
        'id': 'billing',
        'name': 'Billing',
        'icon': 'bi-credit-card',
        'url_name': 'billing:revenue_overview',
        'category': 'core',
        'description': 'Billing and revenue management'
    },
    {
        'id': 'access_control',
        'name': 'Access Control',
        'icon': 'bi-shield-lock',
        'url_name': 'access_control:dashboard',
        'category': 'feature',  # Changed to 'feature' so regular users can see it
        'description': 'Manage permissions, feature toggles, and entitlements'
    },
    # Feature Apps
    {
        'id': 'sales',
        'name': 'Sales',
        'icon': 'bi-graph-up',
        'url_name': 'sales:sales_dashboard',
        'category': 'feature',
        'description': 'Sales pipelines and performance'
    },
    {
        'id': 'leads',
        'name': 'Leads',
        'icon': 'bi-funnel',
        'url_name': 'leads:lead_list',
        'category': 'feature',
        'description': 'Lead management and acquisition'
    },
    {
        'id': 'products',
        'name': 'Products',
        'icon': 'bi-box-seam',
        'url_name': 'products:product_list',
        'category': 'feature',
        'description': 'Product catalog and pricing'
    },
    {
        'id': 'opportunities',
        'name': 'Opportunities',
        'icon': 'bi-lightbulb',
        'url_name': 'opportunities:sales_velocity_dashboard',
        'category': 'feature',
        'description': 'Opportunity tracking and forecasting'
    },
    {
        'id': 'proposals',
        'name': 'Proposals',
        'icon': 'bi-file-text',
        'url_name': 'proposals:proposal_dashboard',
        'category': 'feature',
        'description': 'Quote and proposal management'
    },
    {
        'id': 'cases',
        'name': 'Support Cases',
        'icon': 'bi-headset',
        'url_name': 'cases:case_list',
        'category': 'feature',
        'description': 'Customer support ticketing'
    },
    {
        'id': 'engagement',
        'name': 'Engagement',
        'icon': 'bi-person-lines-fill',
        'url_name': 'engagement:dashboard',
        'category': 'feature',
        'description': 'Customer engagement tracking'
    },
    {
        'id': 'nps',
        'name': 'NPS',
        'icon': 'bi-heart',
        'url_name': 'nps:nps_dashboard',
        'category': 'feature',
        'description': 'Net Promoter Score surveys'
    },
    {
        'id': 'marketing',
        'name': 'Marketing',
        'icon': 'bi-megaphone',
        'url_name': 'marketing:campaign_performance',
        'category': 'feature',
        'description': 'Marketing campaigns and attribution'
    },
    {
        'id': 'reports',
        'name': 'Reports',
        'icon': 'bi-bar-chart-fill',
        'url_name': 'reports:dashboard',
        'category': 'feature',
        'description': 'Analytics and reporting'
    },
    {
        'id': 'automation',
        'name': 'Automation',
        'icon': 'bi-robot',
        'url_name': 'automation:workflow_builder',
        'category': 'feature',
        'description': 'Workflow automation builder'
    },
    {
        'id': 'settings_app',
        'name': 'Settings',
        'icon': 'bi-gear-wide-connected',
        'url_name': 'settings_app:dashboard',
        'category': 'feature',
        'description': 'System configuration'
    },
    {
        'id': 'learn',
        'name': 'Learning',
        'icon': 'bi-book',
        'url_name': 'learn:dashboard',
        'category': 'feature',
        'description': 'LMS and training'
    },
    {
        'id': 'tasks',
        'name': 'Tasks',
        'icon': 'bi-check2-square',
        'url_name': 'tasks:dashboard',
        'category': 'feature',
        'description': 'Task management'
    },
    { 
        'id': 'commissions',
        'name': 'Commissions',
        'icon': 'bi-cash-coin',
        'url_name': 'commissions:dashboard',
        'category': 'feature',
        'description': 'Sales commissions and compensation'
    },
    {
        'id': 'developer',
        'name': 'Developer',
        'icon': 'bi-code-slash',
        'url_name': 'developer:dashboard',
        'category': 'feature',
        'description': 'Developer tools and API access'
    },
    {
        'id':'communication',
        'name':'Communications',
        'icon':'bi-chat-dots',
        'url_name':'communication:dashboard',
        'category':'feature',
        'description':'Email and messaging management'
    },
    # Control Plane Apps
    {
        'id': 'core',
        'name': 'Core',
        'icon': 'bi-gear',
        'url_name': 'core:app_settings',
        'category': 'control',
        'description': 'Core system management'
    },
    {
        'id': 'infrastructure',
        'name': 'Infrastructure',
        'icon': 'bi-server',
        'url_name': 'infrastructure:dashboard',
        'category': 'control',
        'description': 'Server and resource monitoring'
    },
    {
        'id': 'audit_logs',
        'name': 'Audit Logs',
        'icon': 'bi-journal-text',
        'url_name': 'audit_logs:dashboard',
        'category': 'control',
        'description': 'Security and activity logs'
    },
    {
        'id': 'feature_flags',
        'name': 'Feature Flags',
        'icon': 'bi-flag',
        'url_name': 'feature_flags:dashboard',
        'category': 'control',
        'description': 'Feature toggles and management'
    },
    {
        'id': 'global_alerts',
        'name': 'Global Alerts',
        'icon': 'bi-exclamation-triangle',
        'url_name': 'global_alerts:dashboard',
        'category': 'control',
        'description': 'System-wide alerts and incident management'
    },
]

def get_app_by_id(app_id):
    for app in AVAILABLE_APPS:
        if app['id'] == app_id:
            return app
    return None