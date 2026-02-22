from django.core.management.base import BaseCommand
from django.utils import timezone
from invoicing.models import Invoice


class Command(BaseCommand):
    help = 'Check for overdue invoices and update their status'

    def handle(self, *args, **options):
        today = timezone.now().date()
        overdue_invoices = Invoice.objects.filter(
            due_date__lt=today,
            status__in=['sent', 'partial']
        )

        count = overdue_invoices.update(status='overdue')
        self.stdout.write(
            self.style.SUCCESS(f'Marked {count} invoice(s) as overdue.')
        )
