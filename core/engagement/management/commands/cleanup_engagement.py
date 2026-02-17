from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.engagement.models import EngagementEvent

class Command(BaseCommand):
    help = 'Cleans up old engagement events based on age and importance.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Delete events older than this many days (default 365)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = EngagementEvent.objects.filter(
            created_at__lt=cutoff_date,
            is_important=False
        )
        
        count = queryset.count()
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN: Would delete {count} events older than {days} days."))
        else:
            queryset.delete()
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} events older than {days} days."))
