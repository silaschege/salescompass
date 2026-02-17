# Migration to move Invoice, Payment, and related models from billing to invoicing app.
# Uses SeparateDatabaseAndState so that:
# - Django's state (migration registry) reflects model removal from billing
# - The actual database tables are NOT touched (they stay as billing_*)
# The invoicing app's 0001_initial migration will register these models in the new app.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_remove_taxrule_tax_rate_and_more'),
        ('accounts', '0002_initial'),
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Use SeparateDatabaseAndState:
        # - state_operations: tell Django these models no longer belong to billing
        # - database_operations: empty (tables stay in place for invoicing app)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Remove FK fields first to avoid dependency issues
                migrations.RemoveField(
                    model_name='creditadjustment',
                    name='adjustment_type_ref',
                ),
                migrations.RemoveField(
                    model_name='creditadjustment',
                    name='invoice',
                ),
                migrations.RemoveField(
                    model_name='creditadjustment',
                    name='subscription',
                ),
                migrations.RemoveField(
                    model_name='creditadjustment',
                    name='tenant',
                ),
                migrations.RemoveField(
                    model_name='invoice',
                    name='account',
                ),
                migrations.RemoveField(
                    model_name='invoice',
                    name='subscription',
                ),
                migrations.RemoveField(
                    model_name='invoice',
                    name='tenant',
                ),
                migrations.RemoveField(
                    model_name='payment',
                    name='invoice',
                ),
                migrations.RemoveField(
                    model_name='payment',
                    name='payment_method',
                ),
                migrations.RemoveField(
                    model_name='payment',
                    name='tenant',
                ),
                migrations.RemoveField(
                    model_name='paymentmethod',
                    name='provider',
                ),
                migrations.RemoveField(
                    model_name='paymentmethod',
                    name='tenant',
                ),
                migrations.RemoveField(
                    model_name='paymentmethod',
                    name='type_ref',
                ),
                migrations.RemoveField(
                    model_name='paymentmethod',
                    name='user',
                ),
                migrations.RemoveField(
                    model_name='paymentproviderconfig',
                    name='name_ref',
                ),
                migrations.RemoveField(
                    model_name='paymentproviderconfig',
                    name='tenant',
                ),
                migrations.AlterUniqueTogether(
                    name='paymentprovider',
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name='paymentprovider',
                    name='tenant',
                ),
                migrations.AlterUniqueTogether(
                    name='paymenttype',
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name='paymenttype',
                    name='tenant',
                ),
                migrations.AlterUniqueTogether(
                    name='adjustmenttype',
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name='adjustmenttype',
                    name='tenant',
                ),
                # Now delete the models from state
                migrations.DeleteModel(name='CreditAdjustment'),
                migrations.DeleteModel(name='Invoice'),
                migrations.DeleteModel(name='Payment'),
                migrations.DeleteModel(name='PaymentMethod'),
                migrations.DeleteModel(name='PaymentProviderConfig'),
                migrations.DeleteModel(name='PaymentProvider'),
                migrations.DeleteModel(name='PaymentType'),
                migrations.DeleteModel(name='AdjustmentType'),
            ],
            database_operations=[],
        ),
    ]
