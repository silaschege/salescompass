from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from billing.models import Plan
from tenants.models import Tenant

# App Registry with Metadata
ALL_APPS = [
    # Row 1: Customer Facing
    {
        'name': 'Lead',
        'url_name': 'leads:leads_analytics',
        'icon_svg': '<path d="M4 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2H4zm0 1h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z" /><path d="M4 6h12v1H4V6zm0 3h12v1H4V9zm0 3h12v1H4v-1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales', 'marketing'],
        'category': 'customer',
    },
    {
        'name': 'Account',
        'url_name': 'accounts:accounts_kanban',
        'icon_svg': '<path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" /><path d="M2 14s1-1.5 6-1.5S14 14 14 14v1H2v-1z" />',
        'plane': 'application',
        'roles': ['all'],
        'category': 'customer',
    },
    {
        'name': 'Engagements',
        'url_name': 'engagement:dashboard',
        'icon_svg': '<path d="M3.5 0a.5.5 0 0 1 .5.5v.5h8V.5a.5.5 0 0 1 1 0v.5h1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h1V.5a.5.5 0 0 1 .5-.5z" /><path d="M8 3a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0V4a1 1 0 0 1 1-1z" /><path d="M5 7a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0V8a1 1 0 0 1 1-1z" /><path d="M10 7a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0V8a1 1 0 0 1 1-1z" /><path d="M8 11a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0v-2a1 1 0 0 1 1-1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales', 'support'],
        'category': 'customer',
    },
    
    # Row 2: Work / Deal Management
    {
        'name': 'Cases',
        'url_name': 'cases:sla_dashboard',
        'icon_svg': '<path d="M11 5.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5v-1zM11 9a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5v-1z" /><path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4z" /><path d="M3 4.5a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5zm0 4a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5zm0 4a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'support'],
        'category': 'work',
    },
    {
        'name': 'Opportunities',
        'url_name': 'opportunities:kanban',
        'icon_svg': '<path d="M4 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2H4zm0 1h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z" /><path d="M4 6h12v1H4V6zm0 3h12v1H4V9zm0 3h12v1H4v-1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales'],
        'category': 'work',
    },
    {
        'name': 'Proposal',
        'url_name': 'proposals:engagement_dashboard',
        'icon_svg': '<path d="M14 2h-4.5a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5V2.5a.5.5 0 0 0-.5-.5h-4zM6 2H1.5a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5V2.5a.5.5 0 0 0-.5-.5H6zm0 13v-3.5h-.5a.5.5 0 0 0 0 1h.5zM2 4h3v-1H2v1zm0 3h3V6H2v1zm0 2h3V8H2v1zm0 2h3v-1H2v1zm0 2h3v-1H2v1zM10 4h3v-1h-3v1zm0 3h3V6h-3v1zm0 2h3V8h-3v1zm0 2h3v-1h-3v1zm0 2h3v-1h-3v1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales'],
        'category': 'work',
    },
    {
        'name': 'Sale',
        'url_name': 'sales:sales_dashboard',
        'icon_svg': '<path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm3.93 6.588l-7.857 3.428A.5.5 0 0 1 3 9.5v-3a.5.5 0 0 1 .073-.262l7.857-3.428A.5.5 0 0 1 12 3.5v3a.5.5 0 0 1-.07.262z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales'],
        'category': 'work',
    },
    {
        'name': 'Tasks',
        'url_name': 'tasks:list',
        'icon_svg': '<path d="M14 2h-4.5a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5V2.5a.5.5 0 0 0-.5-.5h-4zM6 2H1.5a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5V2.5a.5.5 0 0 0-.5-.5H6zm0 13v-3.5h-.5a.5.5 0 0 0 0 1h.5zM2 4h3v-1H2v1zm0 3h3V6H2v1zm0 2h3V8H2v1zm0 2h3v-1H2v1zm0 2h3v-1H2v1zM10 4h3v-1h-3v1zm0 3h3V6h-3v1zm0 2h3V8h-3v1zm0 2h3v-1h-3v1zm0 2h3v-1h-3v1z" />',
        'plane': 'application',
        'roles': ['all'],
        'category': 'work',
    },
    {
        'name': 'Products',
        'url_name': 'products:product_list',
        'icon_svg': '<path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .491.592l-1.5 8A.5.5 0 0 1 13 12H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5zM3.102 4l1.313 7h8.17l1.313-7H3.102zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />',
        'plane': 'application',
        'roles': ['all'],
        'category': 'work',
    },
    {
        'name': 'Commissions',
        'url_name': 'commissions:list',
        'icon_svg': '<path d="M12 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h8zM4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4z"/><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>',
        'plane': 'application',
        'roles': ['admin', 'manager', 'sales'],
        'category': 'work',
    },

    # Row 3: Support / Analytics
    {
        'name': 'Learn',
        'url_name': 'learn:list',
        'icon_svg': '<path d="M2 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2zm10 1v12H4V2h8z" /><path d="M6 6h4v1H6V6zm0 2h4v1H6V8zm0 2h4v1H6v-1z" />',
        'plane': 'application',
        'roles': ['all'],
        'category': 'analytics',
    },
    {
        'name': 'Reports',
        'url_name': 'reports:dashboard',
        'icon_svg': '<path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2zm4 8a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V9z" /><path d="M7 3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V3z" />',
        'plane': 'application',
        'roles': ['admin', 'manager'],
        'category': 'analytics',
    },
    {
        'name': 'Marketing',
        'url_name': 'marketing:list',
        'icon_svg': '<path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z" /><path d="M6 5h4v1H6V5zm0 2h4v1H6V7zm0 2h4v1H6V9z" /><path d="M6 11h4v1H6v-1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'marketing'],
        'category': 'analytics',
    },
    {
        'name': 'NPS',
        'url_name': 'nps:nps_dashboard',
        'icon_svg': '<path d="M8 4.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5z" /><path d="M4 6a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H5a1 1 0 0 1-1-1z" /><path d="M4 8a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H5a1 1 0 0 1-1-1z" /><path d="M4 10a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H5a1 1 0 0 1-1-1z" /><path d="M4 12a1 1 0 0 1 1-1h6a1 1 0 0 1 0 2H5a1 1 0 0 1-1-1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager', 'marketing'],
        'category': 'analytics',
    },
    {
        'name': 'Dashboard',
        'url_name': 'dashboard:cockpit',
        'icon_svg': '<path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm3.93 6.588l-7.857 3.428A.5.5 0 0 1 3 9.5v-3a.5.5 0 0 1 .073-.262l7.857-3.428A.5.5 0 0 1 12 3.5v3a.5.5 0 0 1-.07.262z" />',
        'plane': 'application',
        'roles': ['all'],
        'category': 'analytics',
    },

    # Row 4: Admin / Config
    {
        'name': 'Settings',
        'url_name': 'settings_app:list',
        'icon_svg': '<path d="M9.243 1.02a1 1 0 0 0-2.486 0l-.272 1.09a5.978 5.978 0 0 0-1.528.88l-1.03-.6a1 1 0 0 0-1.366.366l-.516.894a1 1 0 0 0 .366 1.366l.6 1.03a5.978 5.978 0 0 0-.88 1.528l-1.09.272a1 1 0 0 0 0 2.486l1.09.272a5.978 5.978 0 0 0 .88 1.528l-.6 1.03a1 1 0 0 0 .366 1.366l.894.516a1 1 0 0 0 1.366-.366l1.03-.6a5.978 5.978 0 0 0 1.528.88l.272 1.09a1 1 0 0 0 2.486 0l.272-1.09a5.978 5.978 0 0 0 1.528-.88l1.03.6a1 1 0 0 0 1.366-.366l.516-.894a1 1 0 0 0-.366-1.366l-.6-1.03a5.978 5.978 0 0 0 .88-1.528l1.09-.272a1 1 0 0 0 0-2.486l-1.09-.272a5.978 5.978 0 0 0-.88-1.528l.6-1.03a1 1 0 0 0-.366-1.366l-.894-.516a1 1 0 0 0-1.366.366l-1.03.6a5.978 5.978 0 0 0-1.528-.88l-.272-1.09zM8 10a2 2 0 1 1 0-4 2 2 0 0 1 0 4z" />',
        'plane': 'application',
        'roles': ['admin', 'manager'],
        'category': 'admin',
    },
    {
        'name': 'Automations',
        'url_name': 'automation:list',
        'icon_svg': '<path d="M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 1A5 5 0 1 1 8 3a5 5 0 0 1 0 10z" /><path d="M8 5a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0V6a1 1 0 0 1 1-1z" /><path d="M8 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 8 1z" />',
        'plane': 'application',
        'roles': ['admin', 'manager'],
        'category': 'admin',
    },
    {
        'name': 'Developer',
        'url_name': 'developer:dashboard',
        'icon_svg': '<path d="M9.5 0a.5.5 0 0 1 .5.5.5.5 0 0 0 .5.5.5.5 0 0 1 .5.5V2a.5.5 0 0 1-.5.5h-5A.5.5 0 0 1 5 2v-.5a.5.5 0 0 1 .5-.5.5.5 0 0 0 .5-.5.5.5 0 0 1 .5-.5h3z"/><path d="M3 2.5a.5.5 0 0 1 .5-.5H4a.5.5 0 0 0 0-1h-.5A1.5 1.5 0 0 0 2 2.5v12A1.5 1.5 0 0 0 3.5 16h9a1.5 1.5 0 0 0 1.5-1.5v-12A1.5 1.5 0 0 0 12.5 1H12a.5.5 0 0 0 0 1h.5a.5.5 0 0 1 .5.5v12a.5.5 0 0 1-.5.5h-9a.5.5 0 0 1-.5-.5v-12z"/><path d="M5.854 7.146a.5.5 0 1 0-.708.708L6.793 9.5 5.146 11.146a.5.5 0 0 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2zM9 11.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>',
        'plane': 'application',
        'roles': ['admin', 'manager'],
        'category': 'admin',
    },

    # Control Plane Apps (Available to Superusers/Internal)
    {
        'name': 'Tenants',
        'url_name': 'tenants:list',
        'icon_svg': '<path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
    {
        'name': 'Billing',
        'url_name': 'billing:billing_home',
        'icon_svg': '<path d="M1 3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1H1zm7 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" /><path d="M0 5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V5zm3 0a2 2 0 0 1-2 2v4a2 2 0 0 1 2 2h10a2 2 0 0 1 2-2V7a2 2 0 0 1-2-2H3z" />',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
    {
        'name': 'Infrastructure',
        'url_name': 'infrastructure:dashboard',
        'icon_svg': '<path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm8.5 9.5a.5.5 0 0 0-1 0v1a.5.5 0 0 0 1 0v-1zm1.5-5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0v-6zm1.5-2.5a.5.5 0 0 0-1 0v8.5a.5.5 0 0 0 1 0V4zm1.5 4.5a.5.5 0 0 0-1 0v4a.5.5 0 0 0 1 0V9z" />',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
    {
        'name': 'Audit Logs',
        'url_name': 'audit_logs:dashboard',
        'icon_svg': '<path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-1h1v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v1H1V2a2 2 0 0 1 2-2z"/><path d="M1 5v-.5a.5.5 0 0 1 1 0V5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1H1zm0 3v-.5a.5.5 0 0 1 1 0V8h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1H1zm0 3v-.5a.5.5 0 0 1 1 0v.5h.5a.5.5 0 0 1 0 1h-2a.5.5 0 0 1 0-1H1z"/>',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
    {
        'name': 'Feature Flags',
        'url_name': 'feature_flags:dashboard',
        'icon_svg': '<path d="M2.5 1a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1H3v9a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4h.5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2.5zm2 4h7v8H4.5V5z"/><path d="M6.5 7h3v1h-3V7zm0 2h3v1h-3V9z"/>',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
    {
        'name': 'Global Alerts',
        'url_name': 'global_alerts:dashboard',
        'icon_svg': '<path d="M8 16a2 2 0 0 0 2-2H6a2 2 0 0 0 2 2zm.995-14.901a1 1 0 1 0-1.99 0A5.002 5.002 0 0 0 3 6c0 1.098-.5 6-2 7h14c-1.5-1-2-5.902-2-7 0-2.42-1.72-4.44-4.005-4.901z" />',
        'plane': 'control',
        'roles': ['superuser'],
        'category': 'control',
    },
]

def app_selection(request):
    """
    View to display available apps based on user role and plane.
    """
    user = request.user
    if not user.is_authenticated:
        return redirect('login')

    # Determine User Role
    user_role = 'user'
    if user.is_superuser:
        user_role = 'superuser'
    elif hasattr(user, 'role') and user.role:
        user_role = user.role.name.lower()
    
    # Determine Company Name
    company_name = "Unknown Tenant"
    if user.is_superuser:
        company_name = "SalesCompass Internal"
    elif user.tenant_id:
        try:
            tenant = Tenant.objects.get(id=user.tenant_id)
            company_name = tenant.name
        except (Tenant.DoesNotExist, ValueError):
            company_name = "Unknown Tenant"
    
    # Initialize grouped_apps with all categories
    grouped_apps = {
        'customer': [],
        'work': [],
        'analytics': [],
        'admin': [],
        'control': []
    }
    
    # Filter Apps
    for app in ALL_APPS:
        # 1. Control Plane Check
        if app['plane'] == 'control' and not user.is_superuser:
            continue
        
        # 2. Role Check
        allowed = False
        
        # Superusers see everything (except maybe strictly restricted apps, but usually everything)
        if user.is_superuser:
            allowed = True
        
        # 'all' role allows everyone
        elif 'all' in app['roles']:
            allowed = True
            
        # Check specific roles
        else:
            for role in app['roles']:
                if role in user_role:
                    allowed = True
                    break
        
        if allowed:
            # Add to appropriate category
            category = app.get('category', 'work') # Default to work if missing
            if category in grouped_apps:
                grouped_apps[category].append(app)
            else:
                # Fallback for unknown categories
                grouped_apps['work'].append(app)

    # Check if any apps are available
    has_any_apps = any(grouped_apps.values())

    context = {
        'grouped_apps': grouped_apps,
        'has_any_apps': has_any_apps,
        'user_info': {
            'name': user.get_full_name() or user.email,
            'role': user_role.title(),
            'company': company_name,
        }
    }
    return render(request, 'logged_in/app_selection.html', context)

# California locations from your KB
CALIFORNIA_LOCATIONS = [
    "Bakersfield", "Chico", "Fresno", "Humboldt County", "Imperial County",
    "Inland Empire", "Long Beach", "Los Angeles", "Mendocino", "Merced",
    "Modesto", "Monterey", "North Bay", "Oakland/East Bay", "Orange County",
    "Palm Springs", "Palmdale/lancaster", "Redding", "Sacramento", "San Diego",
    "San Fernando Valley", "San Francisco", "San Gabriel Valley", "San Jose",
    "San Luis Obispo", "San Mateo", "Santa Barbara", "Santa Cruz", "Santa Maria",
    "Siskiyou", "Stockton", "Susanville", "Ventura", "Visalia"
]

def home(request):
    plans = Plan.objects.filter(is_active=True).order_by('price_monthly')
    return render(request, 'public/index.html', {'plans': plans})

def products(request):
    return render(request, 'public/products.html')

def customers(request):
    return render(request, 'public/customer.html', {
        'california_locations': CALIFORNIA_LOCATIONS
    })

def support(request):
    return render(request, 'public/support.html')

def company(request):
    return render(request, 'public/company.html')

def integrations(request):
    return render(request, 'public/integrations.html')

def api_docs(request):
    return render(request, 'public/api.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check for MFA
            if getattr(user, 'mfa_enabled', False):
                # In a real app, generate and send code here
                # For now, we'll just redirect to a verification page (stub)
                return redirect('mfa_verify')
            
            # Role-based redirection
            if user.is_staff:
                return redirect('dashboard:admin_dashboard')
            elif hasattr(user, 'role') and user.role:
                role_name = user.role.name.lower()
                if 'manager' in role_name:
                    return redirect('dashboard:manager_dashboard')
                elif 'support' in role_name:
                    return redirect('dashboard:support_dashboard')
            
            # Default to Cockpit
            return redirect('dashboard:cockpit')
        else:
            messages.error(request, "Invalid email or password.")
            
    return render(request, 'public/login.html')

def mfa_verify(request):
    """
    Stub view for MFA verification.
    """
    if request.method == 'POST':
        code = request.POST.get('code')
        # Mock verification
        if code == '123456':
            messages.success(request, "MFA Verified.")
            return redirect('dashboard:cockpit')
        else:
            messages.error(request, "Invalid code. (Try 123456)")
            
    return render(request, 'public/mfa_verify.html')

def try_free(request):
    if request.method == 'POST':
        # In real app: create trial tenant, send welcome email via Mailcow
        messages.success(request, "Your 14-day trial has started! Check your email.")
        return HttpResponseRedirect(reverse('login'))
    return render(request, 'public/try.html', {
        'california_locations': CALIFORNIA_LOCATIONS
    })

def pricing(request):
    return render(request, 'public/pricing.html')

def solutions(request):
    return render(request, 'public/solutions.html')
