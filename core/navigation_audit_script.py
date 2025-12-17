#!/usr/bin/env python
"""
Navigation Audit Script for SalesCompass CRM
============================================

This script performs a comprehensive navigation audit including:
1. Top-Down Check: Validate all navigation menu links work correctly
2. Bottom-Up Check: Discover orphaned templates not in navigation
3. Generate detailed audit report with recommendations

Usage:
    python navigation_audit_script.py
"""

import os
import sys
import django
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from bs4 import BeautifulSoup

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver
from django.test import Client
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.template.loader import get_template

User = get_user_model()


class NavigationAuditor:
    """Main navigation audit class"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.templates_dir = self.base_dir
        self.all_templates = []
        self.all_urls = {}
        self.navigation_links = []
        self.broken_links = []
        self.working_links = []
        self.orphaned_templates = []
        self.client = Client()
        self.test_user = None
        
    def setup_test_user(self):
        """Login with provided superadmin credentials"""
        try:
            # Use provided superadmin credentials
            email = 'admin@admin.com'
            password = 'password'
            
            try:
                self.test_user = User.objects.get(email=email)
                print(f"✅ Found superadmin: {self.test_user.email}")
            except User.DoesNotExist:
                print(f"❌ User {email} not found in database")
                return
            
            # Login using force_login (most reliable)
            self.client.force_login(self.test_user)
            
            # Verify login worked
            try:
                response = self.client.get('/')
                user = getattr(response.wsgi_request, 'user', None)
                print(f"✅ Logged in as: {user} (Is authenticated: {user.is_authenticated})")
                print(f"   Is superuser: {user.is_superuser}, Is staff: {user.is_staff}")
            except Exception as e:
                print(f"⚠️  Could not verify login: {e}")
        except Exception as e:
            print(f"❌ Error setting up test user: {e}")
    
    def discover_all_templates(self) -> List[str]:
        """Find all HTML templates in the project"""
        print("\n🔍 Phase 1: Discovering Templates")
        print("=" * 60)
        
        templates = []
        for root, dirs, files in os.walk(self.templates_dir):
            # Skip env directory
            if '/env/' in root or '\\env\\' in root:
                continue
            
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.templates_dir)
                    templates.append(rel_path)
        
        self.all_templates = sorted(templates)
        print(f"✅ Found {len(self.all_templates)} templates")
        
        # Group by app
        apps = defaultdict(int)
        for template in self.all_templates:
            if '/templates/' in template:
                app_name = template.split('/')[0]
                apps[app_name] += 1
        
        print(f"\n📊 Templates by App:")
        for app, count in sorted(apps.items(), key=lambda x: x[1], reverse=True):
            print(f"   {app:20s}: {count:3d} templates")
        
        return self.all_templates
    
    def extract_url_patterns(self) -> Dict[str, str]:
        """Extract all URL patterns from Django's URL configuration"""
        print("\n🔍 Phase 2: Extracting URL Patterns")
        print("=" * 60)
        
        url_patterns = {}
        resolver = get_resolver()
        
        def extract_patterns(patterns, namespace=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    # Nested URL patterns (includes)
                    new_namespace = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
                    extract_patterns(pattern.url_patterns, new_namespace)
                elif isinstance(pattern, URLPattern):
                    # Actual URL pattern
                    name = pattern.name
                    if name:
                        full_name = f"{namespace}:{name}" if namespace else name
                        pattern_str = str(pattern.pattern)
                        url_patterns[full_name] = pattern_str
        
        extract_patterns(resolver.url_patterns)
        
        self.all_urls = url_patterns
        print(f"✅ Found {len(url_patterns)} named URL patterns")
        
        # Group by namespace
        namespaces = defaultdict(int)
        for url_name in url_patterns.keys():
            if ':' in url_name:
                namespace = url_name.split(':')[0]
                namespaces[namespace] += 1
            else:
                namespaces['(root)'] += 1
        
        print(f"\n📊 URLs by Namespace:")
        for ns, count in sorted(namespaces.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ns:20s}: {count:3d} URLs")
        
        return url_patterns
    
    def extract_navigation_links(self) -> List[Dict]:
        """Extract all navigation links from base templates"""
        print("\n🔍 Phase 3: Extracting Navigation Links")
        print("=" * 60)
        
        base_templates = [
            'core/templates/logged_in/base.html',
            'dashboard/templates/dashboard/base.html',
        ]
        
        # Also check module-specific base templates
        for template in self.all_templates:
            if template.endswith('/base.html') and '/templates/' in template:
                base_templates.append(template)
        
        base_templates = list(set(base_templates))
        
        navigation_links = []
        
        for template_path in base_templates:
            full_path = self.base_dir / template_path
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all {% url %} tags
                url_pattern = r"{%\s*url\s+['\"]([^'\"]+)['\"](?:\s+[^%]+)?\s*%}"
                matches = re.findall(url_pattern, content)
                
                for url_name in matches:
                    navigation_links.append({
                        'url_name': url_name,
                        'source_template': template_path,
                        'tested': False,
                        'status': 'pending'
                    })
            
            except Exception as e:
                print(f"⚠️  Error reading {template_path}: {e}")
        
        # Remove duplicates
        unique_links = {}
        for link in navigation_links:
            url_name = link['url_name']
            if url_name not in unique_links:
                unique_links[url_name] = link
        
        self.navigation_links = list(unique_links.values())
        print(f"✅ Found {len(self.navigation_links)} unique navigation links")
        
        return self.navigation_links
    
    def test_navigation_links(self) -> Tuple[List, List]:
        """Test all navigation links for functionality"""
        print("\n🔍 Phase 4: Testing Navigation Links")
        print("=" * 60)
        
        working = []
        broken = []
        
        for i, link in enumerate(self.navigation_links, 1):
            url_name = link['url_name']
            
            try:
                # Try to reverse the URL
                from django.urls import reverse, NoReverseMatch
                
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    # Try with common pk values
                    try:
                        url = reverse(url_name, kwargs={'pk': 1})
                    except:
                        broken.append({
                            **link,
                            'status': 'No Reverse Match',
                            'error': f'Cannot resolve URL pattern: {url_name}'
                        })
                        print(f"   [{i}/{len(self.navigation_links)}] ❌ {url_name:50s} - No Reverse Match")
                        continue
                
                # Test the URL
                response = self.client.get(url, follow=True)
                
                if response.status_code == 200:
                    working.append({
                        **link,
                        'status': 'Working',
                        'url': url,
                        'status_code': 200
                    })
                    print(f"   [{i}/{len(self.navigation_links)}] ✅ {url_name:50s} - OK")
                elif response.status_code == 302:
                    # Redirect (possibly to login)
                    working.append({
                        **link,
                        'status': 'Redirect',
                        'url': url,
                        'status_code': 302
                    })
                    print(f"   [{i}/{len(self.navigation_links)}] ⚠️  {url_name:50s} - Redirect (302)")
                else:
                    broken.append({
                        **link,
                        'status': f'HTTP {response.status_code}',
                        'url': url,
                        'status_code': response.status_code
                    })
                    print(f"   [{i}/{len(self.navigation_links)}] ❌ {url_name:50s} - {response.status_code}")
            
            except Exception as e:
                broken.append({
                    **link,
                    'status': 'Error',
                    'error': str(e)
                })
                print(f"   [{i}/{len(self.navigation_links)}] ❌ {url_name:50s} - Error: {e}")
        
        self.working_links = working
        self.broken_links = broken
        
        print(f"\n✅ Working: {len(working)}")
        print(f"❌ Broken: {len(broken)}")
        
        return working, broken
    
    def identify_orphaned_templates(self) -> List[Dict]:
        """Identify templates not linked in navigation"""
        print("\n🔍 Phase 5: Identifying Orphaned Templates")
        print("=" * 60)
        
        # Get all URL names that are in navigation
        navigation_url_names = set(link['url_name'] for link in self.navigation_links)
        
        # Build a lookup of URL name -> URL name (for matching)
        # Also build a reverse lookup: template-like name -> actual URL name
        url_by_short_name = {}
        for url_name in self.all_urls.keys():
            if ':' in url_name:
                namespace, short_name = url_name.split(':', 1)
                # Store with namespace as key
                key = (namespace, short_name)
                url_by_short_name[key] = url_name
                # Also store common variations
                url_by_short_name[(namespace, short_name.replace('_', '-'))] = url_name
                url_by_short_name[(namespace, short_name.replace('-', '_'))] = url_name
        
        # Templates to exclude (fragments, includes, confirmations)
        exclude_patterns = [
            '_card.html',
            '_confirm_delete.html',
            '/includes/',
            '/widgets/',
            'base.html',
            'email_template.html',  # Email templates
            '_form.html',  # May be AJAX forms
        ]
        
        orphaned = []
        
        for template in self.all_templates:
            # Skip excluded patterns
            if any(pattern in template for pattern in exclude_patterns):
                continue
            
            # Skip non-app templates
            if '/templates/' not in template:
                continue
            
            # Extract potential URL name from template path
            # e.g., "leads/templates/leads/analytics.html" -> "leads:analytics"
            parts = template.split('/templates/')
            if len(parts) == 2:
                app_name = parts[0].split('/')[-1]
                template_name = parts[1].replace(f'{app_name}/', '').replace('.html', '')
                
                # Skip index/list templates that might have different URL names
                if template_name in ['list', 'index']:
                    continue
                
                # Look up the actual URL name from registered patterns
                actual_url = None
                possible_names = []
                
                # Try exact match first
                key = (app_name, template_name)
                if key in url_by_short_name:
                    actual_url = url_by_short_name[key]
                
                # Try with underscores/hyphens
                if not actual_url:
                    key = (app_name, template_name.replace('/', '_'))
                    if key in url_by_short_name:
                        actual_url = url_by_short_name[key]
                
                # Try common suffixes
                if not actual_url:
                    for suffix in ['', '_list', '_detail', '_create', '_update', '_delete']:
                        base_name = template_name.replace('/', '_')
                        key = (app_name, base_name + suffix)
                        if key in url_by_short_name:
                            actual_url = url_by_short_name[key]
                            break
                
                # Generate possible URL names for display
                if actual_url:
                    possible_names = [actual_url]
                else:
                    possible_names = [
                        f"{app_name}:{template_name.replace('/', '_')}",
                        f"{app_name}:{template_name.replace('/', '_')}_list",
                    ]
                
                # Check if any possible name is in navigation or all URLs
                found = False
                for name in possible_names:
                    if name in navigation_url_names or name in self.all_urls:
                        found = True
                        break
                
                if not found:
                    orphaned.append({
                        'template': template,
                        'app': app_name,
                        'name': template_name,
                        'possible_urls': possible_names,
                        'actual_url': actual_url  # Will be the matched URL if found
                    })
        
        self.orphaned_templates = orphaned
        print(f"✅ Found {len(orphaned)} potentially orphaned templates")
        
        if orphaned:
            print(f"\n📊 Orphaned Templates by App:")
            orphan_apps = defaultdict(list)
            for orp in orphaned:
                orphan_apps[orp['app']].append(orp['name'])
            
            for app, templates in sorted(orphan_apps.items()):
                print(f"   {app:20s}: {len(templates):3d} orphans")
                for t in templates[:3]:  # Show first 3
                    print(f"      - {t}")
                if len(templates) > 3:
                    print(f"      ... and {len(templates) - 3} more")
        
        return orphaned
    
    def generate_report(self) -> str:
        """Generate comprehensive audit report"""
        print("\n📝 Phase 6: Generating Report")
        print("=" * 60)
        
        report = f"""# Navigation Audit Report
**Generated**: {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project**: SalesCompass CRM

---

## Executive Summary

### Overall Statistics
- **Total Templates**: {len(self.all_templates)}
- **Total URL Patterns**: {len(self.all_urls)}
- **Navigation Links Tested**: {len(self.navigation_links)}
- **Working Links**: {len(self.working_links)} ({len(self.working_links)/len(self.navigation_links)*100:.1f}%)
- **Broken Links**: {len(self.broken_links)} ({len(self.broken_links)/len(self.navigation_links)*100:.1f}%)
- **Orphaned Templates**: {len(self.orphaned_templates)}

### Health Score
"""
        
        health_score = (len(self.working_links) / len(self.navigation_links) * 100) if self.navigation_links else 0
        
        if health_score >= 90:
            report += f"**{health_score:.1f}%** ✅ Excellent\n\n"
        elif health_score >= 75:
            report += f"**{health_score:.1f}%** ⚠️ Good (some fixes needed)\n\n"
        elif health_score >= 50:
            report += f"**{health_score:.1f}%** ⚠️ Fair (significant fixes needed)\n\n"
        else:
            report += f"**{health_score:.1f}%** ❌ Poor (major fixes required)\n\n"
        
        # Broken Links Section
        report += "---\n\n## 🔴 Broken Navigation Links\n\n"
        
        if self.broken_links:
            report += "| # | URL Name | Source Template | Status | Issue |\n"
            report += "|---|----------|-----------------|--------|-------|\n"
            
            for i, link in enumerate(self.broken_links, 1):
                url_name = link['url_name']
                source = link['source_template'].split('/')[-1]
                status = link['status']
                error = link.get('error', link.get('status_code', 'Unknown'))
                report += f"| {i} | `{url_name}` | {source} | {status} | {error} |\n"
        else:
            report += "✅ No broken links found!\n"
        
        report += "\n---\n\n## 🟢 Working Navigation Links\n\n"
        report += f"Total: {len(self.working_links)} links working correctly\n\n"
        
        # Orphaned Templates Section
        report += "---\n\n## 🔍 Orphaned Templates Analysis\n\n"
        
        if self.orphaned_templates:
            # Group by app
            orphan_by_app = defaultdict(list)
            for orp in self.orphaned_templates:
                orphan_by_app[orp['app']].append(orp)
            
            for app in sorted(orphan_by_app.keys()):
                orphans = orphan_by_app[app]
                report += f"\n### {app.title()} ({len(orphans)} orphans)\n\n"
                report += "| Template | Possible URL Names | Recommendation |\n"
                report += "|----------|-------------------|----------------|\n"
                
                for orp in orphans:
                    template_name = orp['name']
                    urls = ', '.join([f"`{u}`" for u in orp['possible_urls'][:2]])
                    
                    # Generate recommendation
                    if any(word in template_name for word in ['dashboard', 'analytics', 'report']):
                        rec = "🟢 Add to navigation"
                    elif any(word in template_name for word in ['builder', 'editor']):
                        rec = "🟢 Add to navigation"
                    elif any(word in template_name for word in ['preview', 'pdf', 'export']):
                        rec = "🟡 Keep as action/API endpoint"
                    else:
                        rec = "🔍 Review manually"
                    
                    report += f"| `{template_name}` | {urls} | {rec} |\n"
        else:
            report += "✅ No orphaned templates found!\n"
        
        # Recommendations Section
        report += "\n---\n\n## 📋 Recommendations\n\n"
        
        if self.broken_links:
            report += "### Priority 1: Fix Broken Links\n\n"
            for link in self.broken_links[:5]:  # Top 5
                report += f"1. **{link['url_name']}**: {link.get('error', link['status'])}\n"
            if len(self.broken_links) > 5:
                report += f"   - ... and {len(self.broken_links) - 5} more\n"
            report += "\n"
        
        # High-value orphans to add
        high_value_orphans = [
            orp for orp in self.orphaned_templates 
            if any(word in orp['name'] for word in ['dashboard', 'analytics', 'builder'])
        ]
        
        if high_value_orphans:
            report += "### Priority 2: Add High-Value Orphans to Navigation\n\n"
            for orp in high_value_orphans[:10]:
                report += f"1. **{orp['app']}**: `{orp['name']}` - Likely a valuable feature\n"
            report += "\n"
        
        report += "### Priority 3: Clean Up\n\n"
        report += "- Review and remove deprecated templates\n"
        report += "- Consolidate duplicate templates\n"
        report += "- Document intentionally orphaned templates\n"
        
        report += "\n---\n\n"
        report += "*End of Report*\n"
        
        return report
    
    def save_report(self, report: str, filename: str = 'NAVIGATION_AUDIT_REPORT.md'):
        """Save the report to file"""
        report_path = self.base_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report saved to: {report_path}")
        return report_path
    
    def run_full_audit(self):
        """Run the complete navigation audit"""
        print("\n" + "=" * 60)
        print("  SALESCOMPASS CRM - NAVIGATION AUDIT")
        print("=" * 60)
        
        # Setup
        self.setup_test_user()
        
        # Phase 1: Discovery
        self.discover_all_templates()
        
        # Phase 2: URL Patterns
        self.extract_url_patterns()
        
        # Phase 3: Navigation Links
        self.extract_navigation_links()
        
        # Phase 4: Test Links
        self.test_navigation_links()
        
        # Phase 5: Find Orphans
        self.identify_orphaned_templates()
        
        # Phase 6: Generate Report
        report = self.generate_report()
        
        # Save Report
        self.save_report(report)
        
        print("\n" + "=" * 60)
        print("  ✅ AUDIT COMPLETE")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - {len(self.working_links)}/{len(self.navigation_links)} links working")
        print(f"   - {len(self.broken_links)} broken links need fixing")
        print(f"   - {len(self.orphaned_templates)} orphaned templates found")
        print(f"\n📄 See NAVIGATION_AUDIT_REPORT.md for details\n")


if __name__ == '__main__':
    auditor = NavigationAuditor()
    auditor.run_full_audit()
