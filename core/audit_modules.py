#!/usr/bin/env python3
"""
Module Implementation Auditor
Automatically audits module implementation against checklists
"""

import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path('/home/silaskimani/Documents/replit/git/salescompass/core')
CHECKLIST_DIR = BASE_DIR / 'checklist'

def check_module_exists(module_name):
    """Check if module directory exists"""
    module_dir = BASE_DIR / module_name
    return module_dir.exists()

def get_module_files(module_name):
    """Get key files from a module"""
    module_dir = BASE_DIR / module_name
    files = {
        'models': module_dir / 'models.py',
        'views': module_dir / 'views.py',
        'urls': module_dir / 'urls.py',
        'admin': module_dir / 'admin.py',
        'forms': module_dir / 'forms.py',
        'utils': module_dir / 'utils.py',
        'services': module_dir / 'services.py',
        'templates': module_dir / 'templates',
        'tests': module_dir / 'tests.py',
    }
    
    existing = {}
    for key, path in files.items():
        if path.exists():
            existing[key] = path
    
    return existing

def count_models(models_file):
    """Count number of model classes in models.py"""
    if not models_file.exists():
        return 0
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Find all class definitions that inherit from models.Model
    pattern = r'class\s+(\w+)\([^)]*models\.Model[^)]*\):'
    matches = re.findall(pattern, content)
    return len(matches)

def count_views(views_file):
    """Count number of view classes/functions in views.py"""
    if not views_file.exists():
        return 0
    
    with open(views_file, 'r') as f:
        content = f.read()
    
    # Count class-based views
    class_views = len(re.findall(r'^class\s+\w+.*View.*:', content, re.MULTILINE))
    # Count function-based views (def functions that take request as first param)
    func_views = len(re.findall(r'^def\s+\w+\s*\([^)]*request', content, re.MULTILINE))
    
    return class_views + func_views

def count_templates(templates_dir):
    """Count number of templates"""
    if not templates_dir.exists():
        return 0
    
    count = 0
    for root, dirs, files in os.walk(templates_dir):
        count += len([f for f in files if f.endswith('.html')])
    
    return count

def audit_module(module_name):
    """Audit a single module"""
    print(f"\n{'='*60}")
    print(f"MODULE: {module_name.upper()}")
    print(f"{'='*60}")
    
    if not check_module_exists(module_name):
        print(f"❌ Module directory not found")
        return {
            'exists': False,
            'models': 0,
            'views': 0,
            'templates': 0,
            'files': []
        }
    
    files = get_module_files(module_name)
    
    stats = {
        'exists': True,
        'models': count_models(files.get('models')) if 'models' in files else 0,
        'views': count_views(files.get('views')) if 'views' in files else 0,
        'templates': count_templates(files.get('templates')) if 'templates' in files else 0,
        'files': list(files.keys())
    }
    
    print(f"✓ Module exists")
    print(f"📁 Files found: {', '.join(stats['files'])}")
    print(f"📊 Models: {stats['models']}")
    print(f"📊 Views: {stats['views']}")
    print(f"📊 Templates: {stats['templates']}")
    
    return stats

# List of all modules to audit
MODULES = [
    'core', 'tenants', 'infrastructure', 'settings_app', 'developer',
    'accounts', 'audit_logs', 'feature_flags',
    'leads', 'opportunities', 'cases', 'tasks', 'engagement',
    'sales', 'products', 'proposals', 'commissions',
    'marketing', 'communication', 'nps',
    'dashboard', 'reports',
    'automation', 'billing', 'global_alerts', 'learn'
]

if __name__ == '__main__':
    print("SalesCompass Module Implementation Audit")
    print("=" * 60)
    
    all_stats = {}
    for module in MODULES:
        all_stats[module] = audit_module(module)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    
    total_modules = len(MODULES)
    existing = sum(1 for s in all_stats.values() if s['exists'])
    total_models = sum(s['models'] for s in all_stats.values())
    total_views = sum(s['views'] for s in all_stats.values())
    total_templates = sum(s['templates'] for s in all_stats.values())
    
    print(f"Total modules checked: {total_modules}")
    print(f"Existing modules: {existing}")
    print(f"Total models: {total_models}")
    print(f"Total views: {total_views}")
    print(f"Total templates: {total_templates}")
