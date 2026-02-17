#!/usr/bin/env python3
"""
Bulk Checklist Updater
Updates all module checklists with current implementation status
"""

from pathlib import Path
import re

BASE_DIR = Path('/home/silaskimani/Documents/replit/git/salescompass/core')
CHECKLIST_DIR = BASE_DIR / 'checklist'

# Module stats from audit
MODULE_STATS = {
    'TENANTS': {'models': 30, 'views': 100, 'templates': 75, 'complete': 97},
    'AUTOMATION': {'models': 4, 'views': 60, 'templates': 38, 'complete': 95},
   'MARKETING': {'models': 0, 'views': 92, 'templates': 84, 'complete': 100},
    'BILLING': {'models': 1, 'views': 85, 'templates': 67, 'complete': 95},
    'ACCOUNTS': {'models': 8, 'views': 30, 'templates': 25, 'complete': 90},
    'LEADS': {'models': 0, 'views': 51, 'templates': 29, 'complete': 85},
    'OPPORTUNITIES': {'models': 0, 'views': 25, 'templates': 19, 'complete': 80},
    'TASKS': {'models': 0, 'views': 49, 'templates': 37, 'complete': 90},
    'ENGAGEMENT': {'models': 3, 'views': 38, 'templates': 28, 'complete': 85},
    'SALES': {'models': 6, 'views': 15, 'templates': 12, 'complete': 85},
    'PRODUCTS': {'models': 0, 'views': 26, 'templates': 22, 'complete': 80},
    'PROPOSALS': {'models': 1, 'views': 32, 'templates': 25, 'complete': 85},
    'COMMISSIONS': {'models': 0, 'views': 30, 'templates': 25, 'complete': 85},
    'CASES': {'models': 0, 'views': 17, 'templates': 17, 'complete': 75},
    'DASHBOARD': {'models': 0, 'views': 16, 'templates': 38, 'complete': 80},
    'REPORTS': {'models': 0, 'views': 28, 'templates': 18, 'complete': 75},
    'AUDIT_LOGS': {'models': 6, 'views': 11, 'templates': 12, 'complete': 90},
    'FEATURE_FLAGS': {'models': 6, 'views': 15, 'templates': 15, 'complete': 90},
    'GLOBAL_ALERTS': {'models': 5, 'views': 17, 'templates': 21, 'complete': 85},
    'LEARN': {'models': 0, 'views': 21, 'templates': 18, 'complete': 80},
    'NPS': {'models': 0, 'views': 21, 'templates': 21, 'complete': 85},
    'COMMUNICATION': {'models': 5, 'views': 0, 'templates': 0, 'complete': 50},
    'INFRASTRUCTURE': {'models': 18, 'views': 27, 'templates': 15, 'complete': 80},
    'SETTINGS_APP': {'models': 0, 'views': 122, 'templates': 33, 'complete': 90},
    'DEVELOPER': {'models': 0, 'views': 13, 'templates': 10, 'complete': 70},
    'CORE': {'models': 24, 'views': 32, 'templates': 71, 'complete': 90},
}

def update_review_status(module_name):
    """Update the review status section in a checklist"""
    checklist_file = CHECKLIST_DIR / f"{module_name}_MODULE_MASTER_CHECKLIST.md"
    
    if not checklist_file.exists():
        print(f"❌ {module_name}: Checklist not found")
        return False
    
    with open(checklist_file, 'r') as f:
        content = f.read()
    
    stats = MODULE_STATS.get(module_name, {})
    if not stats:
        print(f"⚠️  {module_name}: No stats available")
        return False
    
    # Update review status section
    new_status = f"""## Review Status
- Last reviewed: 2025-12-28
- Implementation Status: **{stats['complete']}% Complete** ({stats['models']} models, {stats['views']} views, {stats['templates']} templates)"""
    
    # Find and replace review status
    pattern = r'## Review Status\n- Last reviewed: [^\n]+(?:\n- Implementation Status: [^\n]+)?'
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_status, content)
        
        with open(checklist_file, 'w') as f:
            f.write(content)
        
        print(f"✅ {module_name}: Updated ({stats['complete']}% complete)")
        return True
    else:
        print(f"⚠️  {module_name}: Review status section not found")
        return False

# Update all checklists
print("Bulk Updating Module Checklists")
print("=" * 60)

updated = 0
for module in sorted(MODULE_STATS.keys()):
    if update_review_status(module):
        updated += 1

print(f"\n{'=' * 60}")
print(f"Updated {updated} of {len(MODULE_STATS)} checklists")
