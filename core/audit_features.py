#!/usr/bin/env python3
"""
Detailed Module Feature Auditor
Examines actual features implemented in each module
"""

import os
import re
from pathlib import Path

BASE_DIR = Path('/home/silaskimani/Documents/replit/git/salescompass/core')

def get_model_names(models_file):
    """Extract model class names"""
    if not models_file.exists():
        return []
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    pattern = r'class\s+(\w+)\([^)]*models\.Model[^)]*\):'
    return re.findall(pattern, content)

def get_view_names(views_file):
    """Extract view class names"""
    if not views_file.exists():
        return []
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    # Class-based views
    pattern = r'^class\s+(\w+).*View.*:'
    return re.findall(pattern, content, re.MULTILINE)

def has_feature(module_dir, feature_keyword):
    """Check if a feature exists in module files"""
    keywords = feature_keyword.lower().split()
    
    for file_path in module_dir.rglob('*.py'):
        try:
            with open(file_path, 'r') as f:
                content = f.read().lower()
                if all(kw in content for kw in keywords):
                    return True
        except:
            pass
    
    return False

def audit_module_features(module_name):
    """Detailed feature audit for a module"""
    module_dir = BASE_DIR / module_name
    
    if not module_dir.exists():
        return None
    
    features = {
        'models': get_model_names(module_dir / 'models.py'),
        'views': get_view_names(module_dir / 'views.py'),
        'has_urls': (module_dir / 'urls.py').exists(),
        'has_admin': (module_dir / 'admin.py').exists(),
        'has_forms': (module_dir / 'forms.py').exists(),
        'has_utils': (module_dir / 'utils.py').exists(),
        'has_services': (module_dir / 'services.py').exists(),
        'has_tests': (module_dir / 'tests.py').exists(),
        'has_templates': (module_dir / 'templates').exists(),
    }
    
    # Check for specific features
    features['has_api'] = has_feature(module_dir, 'api serializer')
    features['has_signals'] = has_feature(module_dir, 'signals')
    features['has_permissions'] = has_feature(module_dir, 'permission')
    features['has_middleware'] = (module_dir / 'middleware.py').exists()
    features['has_management_commands'] = (module_dir / 'management').exists()
    
    return features

# Audit all modules
modules = [
    'tenants', 'automation', 'marketing', 'billing', 'accounts',
    'leads', 'opportunities', 'tasks', 'engagement', 'sales',
    'products', 'proposals', 'commissions', 'cases',
    'dashboard', 'reports', 'audit_logs', 'feature_flags',
    'global_alerts', 'learn', 'nps', 'communication',
    'infrastructure', 'settings_app', 'developer', 'core'
]

print("DETAILED MODULE FEATURE AUDIT")
print("=" * 70)

for module in modules:
    features = audit_module_features(module)
    if features:
        print(f"\n{module.upper()}:")
        print(f"  Models: {len(features['models'])} - {', '.join(features['models'][:5])}{' ...' if len(features['models']) > 5 else ''}")
        print(f"  Views: {len(features['views'])}")
        components = []
        if features['has_urls']: components.append('URLs')
        if features['has_admin']: components.append('Admin')
        if features['has_forms']: components.append('Forms')
        if features['has_utils']: components.append('Utils')
        if features['has_services']: components.append('Services')
        if features['has_api']: components.append('API')
        if features['has_signals']: components.append('Signals')
        if features['has_permissions']: components.append('Permissions')
        if features['has_middleware']: components.append('Middleware')
        if features['has_management_commands']: components.append('Commands')
        print(f"  Components: {', '.join(components)}")
