
"""
Central registry of available applications for the App Permissons system.
Used to populate the App Settings page and validate permissions.
"""
# Define which categories are superuser-only
SUPERUSER_ONLY_CATEGORIES = ['control']

AVAILABLE_APPS = [
    # Core Apps
    {
        'id': 'leads',
        'name': 'Leads',
        'icon': 'bi-funnel',
        'url_name': 'leads:lead_list',
        'category': 'core',
        'description': 'Lead management and acquisition',
        'keywords': 'lead capture scoring qualification nurture conversion prospect pipeline assignment'
    },
    {
        'id': 'dashboard',
        'name': 'Dashboard',
        'icon': 'bi-speedometer2',
        'url_name': 'dashboard:cockpit',
        'category': 'core',
        'description': 'Main unified dashboard',
        'keywords': 'cockpit overview metrics KPI analytics summary charts graphs performance'
    },
    {
        'id': 'accounts',
        'name': 'Accounts',
        'icon': 'bi-briefcase',
        'url_name': 'accounts:account_list',
        'category': 'feature',
        'description': 'Manage customer accounts',
        'keywords': 'customer client company organization contacts hierarchy parent child account'
    },
    {
        'id': 'billing',
        'name': 'Billing',
        'icon': 'bi-credit-card',
        'url_name': 'billing:portal',
        'category': 'core',
        'description': 'Billing and revenue management',
        'keywords': 'subscription invoice payment plan upgrade downgrade usage metering stripe'
    },
    {
        'id': 'invoicing',
        'name': 'Invoicing',
        'icon': 'bi-file-earmark-text',
        'url_name': 'invoicing:invoice_list',
        'category': 'feature',
        'description': 'Customer invoicing and payments',
        'keywords': 'invoice payment accounting billing customer transaction accounts receivable'
    },
    {
        'id': 'accounting',
        'name': 'Accounting',
        'icon': 'bi-journal-text',
        'url_name': 'accounting:dashboard',
        'category': 'feature',
        'description': 'General Ledger and Financial Reporting',
        'keywords': 'journal entry trial balance chart of accounts ledger fiscal year accounts payable accounts receivable bank reconciliation GL debit credit posting'
    },
    {
        'id': 'purchasing',
        'name': 'Purchasing',
        'icon': 'bi-bag-plus',
        'url_name': 'purchasing:dashboard',
        'category': 'feature',
        'description': 'Purchase Orders and Supplier Management',
        'keywords': 'purchase order PO GRN goods receipt note supplier invoice three-way match procurement requisition vendor bill'
    },
    {
        'id': 'suppliers',
        'name': 'Suppliers',
        'icon': 'bi-building-gear',
        'url_name': 'suppliers:supplier_list',
        'category': 'feature',
        'description': 'Vendor and supplier management',
        'keywords': 'vendor supplier performance scorecard documents categories sourcing procurement'
    },
    {
        'id': 'loyalty',
        'name': 'Loyalty',
        'icon': 'bi-award',
        'url_name': 'loyalty:dashboard',
        'category': 'feature',
        'description': 'Customer Rewards and Points Program',
        'keywords': 'points rewards tier program member redemption earn burn loyalty card'
    },
    {
        'id': 'expenses',
        'name': 'Expenses',
        'icon': 'bi-receipt',
        'url_name': 'expenses:dashboard',
        'category': 'feature',
        'description': 'Expense Tracking and Reimbursements',
        'keywords': 'expense report receipt reimbursement mileage per diem travel approval policy'
    },
    {
        'id': 'hr',
        'name': 'HR',
        'icon': 'bi-people',
        'url_name': 'hr:dashboard',
        'category': 'feature',
        'description': 'Employee Management and HR',
        'keywords': 'employee payroll attendance leave vacation PTO benefits onboarding offboarding salary timesheet'
    },
    {
        'id': 'assets',
        'name': 'Assets',
        'icon': 'bi-building',
        'url_name': 'assets:dashboard',
        'category': 'feature',
        'description': 'Fixed Asset Register and Depreciation',
        'keywords': 'fixed asset depreciation disposal acquisition register NBV book value straight line'
    },

    # Feature Apps
    {
        'id': 'sales',
        'name': 'Sales',
        'icon': 'bi-graph-up',
        'url_name': 'sales:sales_dashboard',
        'category': 'feature',
        'description': 'Sales pipelines and performance',
        'keywords': 'pipeline quota forecast territory assignment target commission revenue performance'
    },
    {
        'id': 'customer_portal',
        'name': 'Client Portal',
        'icon': 'bi-person-badge',
        'url_name': 'customer_portal:dashboard',
        'category': 'feature',
        'description': 'Client-facing portal for invoices and support',
        'keywords': 'client portal self-service invoice download ticket support customer login'
    },
    { 
        'id': 'products',
        'name': 'Products',
        'icon': 'bi-box-seam',
        'url_name': 'products:product_list',
        'category': 'feature',
        'description': 'Product catalog and pricing',
        'keywords': 'product catalog SKU pricing variant category bundle kit BOM item'
    },
    {
        'id': 'pos',
        'name': 'Point of Sale',
        'icon': 'bi-display',
        'url_name': 'pos:terminal_list',
        'category': 'feature',
        'description': 'POS Terminal for retail sales',
        'keywords': 'point of sale POS terminal register cash drawer receipt barcode retail checkout'
    },
    {
        'id': 'inventory',
        'name': 'Inventory',
        'icon': 'bi-boxes',
        'url_name': 'inventory:dashboard',
        'category': 'feature',
        'description': 'Stock management and transfers',
        'keywords': 'stock transfer warehouse bin location serial number lot tracking inventory adjustment count reorder'
    },
    {
        'id': 'manufacturing',
        'name': 'MRP',
        'icon': 'bi-tools',
        'url_name': 'manufacturing:dashboard',
        'category': 'feature',
        'description': 'Manufacturing and Work Orders',
        'keywords': 'manufacturing work order BOM bill of materials production routing MRP planning'
    },
    {
        'id': 'logistics',
        'name': 'Logistics',
        'icon': 'bi-truck',
        'url_name': 'logistics:dashboard',
        'category': 'feature',
        'description': 'Shipping, Fulfillment and Tracking',
        'keywords': 'shipping fulfillment tracking carrier delivery route dispatch pickup drop-off freight'
    },
    {
        'id': 'quality_control',
        'name': 'Quality',
        'icon': 'bi-check2-all',
        'url_name': 'quality_control:dashboard',
        'category': 'feature',
        'description': 'Quality Management and Inspections',
        'keywords': 'quality control QC inspection NCR non-conformance defect checklist CAPA AQL sampling'
    },
    {
        'id': 'opportunities',
        'name': 'Opportunities',
        'icon': 'bi-lightbulb',
        'url_name': 'opportunities:sales_velocity_dashboard',
        'category': 'feature',
        'description': 'Opportunity tracking and forecasting',
        'keywords': 'opportunity deal pipeline stage probability forecast close date win loss weighted'
    },
    {
        'id': 'proposals',
        'name': 'Proposals',
        'icon': 'bi-file-text',
        'url_name': 'proposals:proposal_dashboard',
        'category': 'feature',
        'description': 'Quote and proposal management',
        'keywords': 'proposal quote quotation RFP RFQ bid estimate pricing template document'
    },
    {
        'id': 'cases',
        'name': 'Support Cases',
        'icon': 'bi-headset',
        'url_name': 'cases:case_list',
        'category': 'feature',
        'description': 'Customer support ticketing',
        'keywords': 'support case ticket issue resolution SLA helpdesk customer service escalation'
    },
    {
        'id': 'engagement',
        'name': 'Engagement',
        'icon': 'bi-person-lines-fill',
        'url_name': 'engagement:dashboard',
        'category': 'feature',
        'description': 'Customer engagement tracking',
        'keywords': 'engagement touchpoint interaction activity timeline history communication data quality'
    },
    {
        'id': 'nps',
        'name': 'NPS',
        'icon': 'bi-heart',
        'url_name': 'nps:nps_dashboard',
        'category': 'feature',
        'description': 'Net Promoter Score surveys',
        'keywords': 'NPS net promoter score survey feedback satisfaction detractor promoter passive'
    },
    {
        'id': 'marketing',
        'name': 'Marketing',
        'icon': 'bi-megaphone',
        'url_name': 'marketing:campaign_performance',
        'category': 'feature',
        'description': 'Marketing campaigns and attribution',
        'keywords': 'campaign email marketing automation attribution lead source ROI conversion funnel'
    },
    {
        'id': 'reports',
        'name': 'Reports',
        'icon': 'bi-bar-chart-fill',
        'url_name': 'reports:dashboard',
        'category': 'feature',
        'description': 'Analytics and reporting',
        'keywords': 'report analytics dashboard chart visualization export PDF Excel CSV data'
    },
    {
        'id': 'automation',
        'name': 'Automation',
        'icon': 'bi-robot',
        'url_name': 'automation:workflow_builder',
        'category': 'feature',
        'description': 'Workflow automation builder',
        'keywords': 'workflow automation trigger action rule condition schedule email notification'
    },
    {
        'id': 'settings_app',
        'name': 'Settings',
        'icon': 'bi-gear-wide-connected',
        'url_name': 'settings_app:dashboard',
        'category': 'feature',
        'description': 'System configuration',
        'keywords': 'settings configuration preferences system options customize'
    },
    {
        'id': 'learn',
        'name': 'Learning',
        'icon': 'bi-book',
        'url_name': 'learn:dashboard',
        'category': 'feature',
        'description': 'LMS and training',
        'keywords': 'learning LMS training course certification quiz module lesson onboarding'
    },
    {
        'id': 'tasks',
        'name': 'Tasks',
        'icon': 'bi-check2-square',
        'url_name': 'tasks:dashboard',
        'category': 'feature',
        'description': 'Task management',
        'keywords': 'task todo checklist assignment due date priority reminder follow-up'
    },
    { 
        'id': 'commissions',
        'name': 'Commissions',
        'icon': 'bi-cash-coin',
        'url_name': 'commissions:dashboard',
        'category': 'feature',
        'description': 'Sales commissions and compensation',
        'keywords': 'commission sales compensation plan bonus tier payout earnings statement'
    },
    {
        'id': 'projects',
        'name': 'Projects',
        'icon': 'bi-stack',
        'url_name': 'projects:dashboard',
        'category': 'feature',
        'description': 'Project accounting and PSA',
        'keywords': 'project timesheet milestone WBS work breakdown billing budget resource allocation'
    },
    {
        'id': 'developer',
        'name': 'Developer',
        'icon': 'bi-code-slash',
        'url_name': 'developer:dashboard',
        'category': 'feature',
        'description': 'Developer tools and API access',
        'keywords': 'developer API webhook integration token sandbox documentation REST'
    },
    {
        'id':'communication',
        'name':'Communications',
        'icon':'bi-chat-dots',
        'url_name':'communication:dashboard',
        'category':'feature',
        'description':'Email and messaging management',
        'keywords': 'email SMS text message template inbox outbox thread conversation'
    },
    {
        'id': 'wazo',
        'name': 'ReachOut',
        'icon': 'bi-telephone-outbound',
        'url_name': 'wazo:status',
        'category': 'feature',
        'description': 'Telephony and SMS services',
        'keywords': 'telephony call phone SMS text voice VoIP dialer click-to-call call log'
    },
    {
        'id': 'ecommerce',
        'name': 'Storefront',
        'icon': 'bi-shop',
        'url_name': 'ecommerce:index',
        'category': 'feature',
        'description': 'External ecommerce portal and product catalog',
        'keywords': 'ecommerce storefront shop cart checkout order catalog online store'
    },
    # Control Plane Apps
    {
        'id': 'tenants',
        'name': 'Tenants',
        'icon': 'bi-building',
        'url_name': 'tenants:tenant_list',
        'category': 'control',
        'description': 'Manage tenants',
        'keywords': 'tenant organization company provisioning onboarding subdomain clone lifecycle'
    },
    {
        'id': 'core',
        'name': 'Core',
        'icon': 'bi-gear',
        'url_name': 'core:app_settings',
        'category': 'control',
        'description': 'Core system management',
        'keywords': 'core system management app permissions module configuration'
    },
    {
        'id': 'infrastructure',
        'name': 'Infrastructure',
        'icon': 'bi-server',
        'url_name': 'infrastructure:dashboard',
        'category': 'control',
        'description': 'Server and resource monitoring',
        'keywords': 'infrastructure server monitoring CPU memory disk health status uptime'
    },
    {
        'id': 'audit_logs',
        'name': 'Audit Logs',
        'icon': 'bi-journal-text',
        'url_name': 'audit_logs:dashboard',
        'category': 'control',
        'description': 'Security and activity logs',
        'keywords': 'audit log security activity tracking change history user action compliance'
    },
    {
        'id': 'feature_flags',
        'name': 'Feature Flags',
        'icon': 'bi-flag',
        'url_name': 'feature_flags:dashboard',
        'category': 'control',
        'description': 'Feature toggles and management',
        'keywords': 'feature flag toggle rollout A/B testing canary release experiment'
    },
    {
        'id': 'global_alerts',
        'name': 'Global Alerts',
        'icon': 'bi-exclamation-triangle',
        'url_name': 'global_alerts:dashboard',
        'category': 'control',
        'description': 'System-wide alerts and incident management',
        'keywords': 'alert notification incident warning error system-wide broadcast announcement'
    },
    {
        'id': 'access_control',
        'name': 'Access Control',
        'icon': 'bi-shield-lock',
        'url_name': 'access_control:dashboard',
        'category': 'control',
        'description': 'Manage permissions, feature toggles, and entitlements',
        'keywords': 'access control permission role RBAC entitlement feature toggle security authorization'
    },
]

def get_app_by_id(app_id):
    for app in AVAILABLE_APPS:
        if app['id'] == app_id:
            return app
    return None