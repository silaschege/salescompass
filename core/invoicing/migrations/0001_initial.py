# Initial migration for the invoicing app.
# Uses SeparateDatabaseAndState so that:
# - Django's state registers these models under the invoicing app
# - The actual database tables are NOT re-created (they already exist as billing_*)
# All models use db_table = 'billing_*' to reference the original tables.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('billing', '0006_move_models_to_invoicing'),
        ('accounts', '0002_initial'),
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='AdjustmentType',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('type_name', models.CharField(db_index=True, help_text="e.g., 'credit', 'refund'", max_length=20)),
                        ('label', models.CharField(max_length=50)),
                        ('order', models.IntegerField(default=0)),
                        ('type_is_active', models.BooleanField(default=True, help_text='Whether this type is active')),
                        ('is_system', models.BooleanField(default=False)),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'verbose_name_plural': 'Adjustment Types',
                        'ordering': ['order', 'type_name'],
                        'unique_together': {('tenant', 'type_name')},
                        'db_table': 'billing_adjustmenttype',
                    },
                ),
                migrations.CreateModel(
                    name='PaymentProvider',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('provider_name', models.CharField(db_index=True, help_text="e.g., 'stripe', 'paypal'", max_length=50)),
                        ('label', models.CharField(max_length=100)),
                        ('order', models.IntegerField(default=0)),
                        ('provider_is_active', models.BooleanField(default=True, help_text='Whether this provider is active')),
                        ('is_system', models.BooleanField(default=False)),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'verbose_name_plural': 'Payment Providers',
                        'ordering': ['order', 'provider_name'],
                        'unique_together': {('tenant', 'provider_name')},
                        'db_table': 'billing_paymentprovider',
                    },
                ),
                migrations.CreateModel(
                    name='PaymentType',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('type_name', models.CharField(db_index=True, help_text="e.g., 'card', 'mobile_money'", max_length=20)),
                        ('label', models.CharField(max_length=50)),
                        ('order', models.IntegerField(default=0)),
                        ('type_is_active', models.BooleanField(default=True, help_text='Whether this type is active')),
                        ('is_system', models.BooleanField(default=False)),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'verbose_name_plural': 'Payment Types',
                        'ordering': ['order', 'type_name'],
                        'unique_together': {('tenant', 'type_name')},
                        'db_table': 'billing_paymenttype',
                    },
                ),
                migrations.CreateModel(
                    name='PaymentProviderConfig',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('provider_config_name', models.CharField(choices=[('stripe', 'Stripe'), ('mpesa', 'M-Pesa'), ('paypal', 'PayPal'), ('flutterwave', 'Flutterwave'), ('paystack', 'Paystack')], help_text="e.g., 'stripe', 'paypal'", max_length=50, unique=True)),
                        ('display_name', models.CharField(max_length=100)),
                        ('api_key', models.TextField()),
                        ('secret_key', models.TextField()),
                        ('webhook_secret', models.TextField()),
                        ('config_is_active', models.BooleanField(default=True)),
                        ('config_created_at', models.DateTimeField(auto_now_add=True)),
                        ('config_updated_at', models.DateTimeField(auto_now=True)),
                        ('name_ref', models.ForeignKey(blank=True, help_text='Dynamic provider (replaces name field)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='configs', to='invoicing.paymentprovider')),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'db_table': 'billing_paymentproviderconfig',
                    },
                ),
                migrations.CreateModel(
                    name='Invoice',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('invoice_number', models.CharField(max_length=50, unique=True)),
                        ('status', models.CharField(choices=[('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid'), ('void', 'Void'), ('overdue', 'Overdue')], default='draft', max_length=20)),
                        ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('due_date', models.DateField()),
                        ('issued_date', models.DateField(auto_now_add=True)),
                        ('stripe_invoice_id', models.CharField(blank=True, max_length=100)),
                        ('pdf_url', models.URLField(blank=True)),
                        ('invoice_is_active', models.BooleanField(default=True)),
                        ('invoice_created_at', models.DateTimeField(auto_now_add=True)),
                        ('invoice_updated_at', models.DateTimeField(auto_now=True)),
                        ('account', models.ForeignKey(blank=True, help_text='Account associated with this invoice', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='accounts.account')),
                        ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='billing.subscription')),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'db_table': 'billing_invoice',
                    },
                ),
                migrations.CreateModel(
                    name='PaymentMethod',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('type', models.CharField(choices=[('card', 'Credit/Debit Card'), ('mobile_money', 'Mobile Money'), ('bank_account', 'Bank Account'), ('wallet', 'Digital Wallet')], max_length=20)),
                        ('display_info', models.CharField(help_text="Masked display info (e.g., '**** 4242', '+254 *** 1234')", max_length=100)),
                        ('provider_payment_method_id', models.CharField(max_length=100)),
                        ('is_default', models.BooleanField(default=False)),
                        ('payment_method_is_active', models.BooleanField(default=True)),
                        ('method_created_at', models.DateTimeField(auto_now_add=True)),
                        ('method_updated_at', models.DateTimeField(auto_now=True)),
                        ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='invoicing.paymentproviderconfig')),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                        ('type_ref', models.ForeignKey(blank=True, help_text='Dynamic payment type (replaces type field)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payment_methods', to='invoicing.paymenttype')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'billing_paymentmethod',
                    },
                ),
                migrations.CreateModel(
                    name='Payment',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('status', models.CharField(choices=[('pending', 'Pending'), ('succeeded', 'Succeeded'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                        ('stripe_payment_intent_id', models.CharField(blank=True, max_length=100)),
                        ('transaction_id', models.CharField(blank=True, max_length=100)),
                        ('processed_at', models.DateTimeField(blank=True, null=True)),
                        ('payment_is_active', models.BooleanField(default=True)),
                        ('payment_created_at', models.DateTimeField(auto_now_add=True)),
                        ('payment_updated_at', models.DateTimeField(auto_now=True)),
                        ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='invoicing.invoice')),
                        ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='invoicing.paymentmethod')),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'db_table': 'billing_payment',
                    },
                ),
                migrations.CreateModel(
                    name='CreditAdjustment',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('adjustment_type', models.CharField(choices=[('credit', 'Credit'), ('refund', 'Refund'), ('discount', 'Discount')], max_length=20)),
                        ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('adjustment_description', models.TextField()),
                        ('applied_date', models.DateTimeField(auto_now_add=True)),
                        ('adjustment_is_active', models.BooleanField(default=True)),
                        ('adjustment_created_at', models.DateTimeField(auto_now_add=True)),
                        ('adjustment_updated_at', models.DateTimeField(auto_now=True)),
                        ('adjustment_type_ref', models.ForeignKey(blank=True, help_text='Dynamic adjustment type (replaces adjustment_type field)', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='credit_adjustments', to='invoicing.adjustmenttype')),
                        ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='credit_adjustments', to='invoicing.invoice')),
                        ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_adjustments', to='billing.subscription')),
                        ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='tenants.tenant')),
                    ],
                    options={
                        'db_table': 'billing_creditadjustment',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
