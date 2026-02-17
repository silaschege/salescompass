import os
import django
import sys

# Setup Django environment
sys.path.append('/home/silaskimani/Documents/salescompass/salescompass')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salescompass.settings')
django.setup()

from dashboard.models import DashboardWidget

def setup_widgets():
    print("Setting up dashboard widgets...")
    
    widgets = [
        {
            'widget_type': 'revenue',
            'name': 'Revenue Chart',
            'description': 'Monthly revenue overview',
            'category': 'revenue',
            'template_path': 'dashboard/widgets/revenue.html',
            'default_span': 6
        },
        {
            'widget_type': 'pipeline',
            'name': 'Sales Pipeline',
            'description': 'Opportunities by stage',
            'category': 'opportunities',
            'template_path': 'dashboard/widgets/pipeline.html',
            'default_span': 6
        },
        {
            'widget_type': 'tasks',
            'name': 'My Tasks',
            'description': 'Upcoming tasks',
            'category': 'tasks',
            'template_path': 'dashboard/widgets/tasks.html',
            'default_span': 4
        },
        {
            'widget_type': 'leads',
            'name': 'Recent Leads',
            'description': 'New leads list',
            'category': 'leads',
            'template_path': 'dashboard/widgets/leads.html',
            'default_span': 4
        },
        {
            'widget_type': 'activity',
            'name': 'Activity Feed',
            'description': 'Recent system activity',
            'category': 'general',
            'template_path': 'dashboard/widgets/activity.html',
            'default_span': 4
        }
    ]

    for w_data in widgets:
        widget, created = DashboardWidget.objects.get_or_create(
            widget_type=w_data['widget_type'],
            defaults=w_data
        )
        if created:
            print(f"Created widget: {widget.name}")
        else:
            print(f"Widget exists: {widget.name}")

    print("Widget setup complete.")

if __name__ == '__main__':
    setup_widgets()
