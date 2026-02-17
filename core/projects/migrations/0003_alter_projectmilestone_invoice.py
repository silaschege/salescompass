# State-only migration: The FK column in the database already points to billing_invoice,
# which is the same table used by invoicing.Invoice (via db_table = 'billing_invoice').
# We only need to update Django's migration state to reference invoicing.Invoice.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoicing', '0001_initial'),
        ('projects', '0002_timesheet_timesheetentry'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='projectmilestone',
                    name='invoice',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='milestones', to='invoicing.invoice'),
                ),
            ],
            database_operations=[],
        ),
    ]
