from django.core.management.base import BaseCommand
from dashboard.models import DashboardWidget

class Command(BaseCommand):
    help = 'Update existing dashboard widgets with appropriate icons'

    def handle(self, *args, **kwargs):
        # Icon mapping for widget types
        WIDGET_ICONS = {
            'revenue': 'bi-graph-up-arrow',
            'pipeline': 'bi-funnel',
            'tasks': 'bi-list-check',
            'leads': 'bi-person-plus',
            'nps': 'bi-emoji-smile',
            'cases': 'bi-ticket-detailed',
            'activity': 'bi-clock-history',
            'leaderboard': 'bi-trophy',
        }
        
        updated = 0
        for widget in DashboardWidget.objects.all():
            if widget.widget_type in WIDGET_ICONS:
                widget.icon = WIDGET_ICONS[widget.widget_type]
                widget.save()
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {widget.name} with icon {widget.icon}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated} widgets with icons')
        )
