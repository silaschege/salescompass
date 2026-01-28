import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from core.models import User
from tenants.models import Tenant
from accounting.models import ChartOfAccount, JournalEntry, AccountingIntegration, FiscalYear
from billing.models import Plan, Subscription, Invoice, Payment, PlanTier
from pos.models import POSTerminal, POSTransaction, POSPayment
from inventory.models import Warehouse

class Command(BaseCommand):
    help = 'Seed test transactions for accounting verification'

    def handle(self, *args, **options):
        self.stdout.write("Starting accounting test data seeding...")

        try:
            with transaction.atomic():
                # 1. Setup Tenant
                tenant, created = Tenant.objects.get_or_create(
                    schema_name='test_accounting_tenant',
                    defaults={'name': 'Accounting Test Co'}
                )
                if created:
                    self.stdout.write(f"Created tenant: {tenant.name}")

                # 2. Setup User
                user = User.objects.filter(tenant=tenant).first()
                if not user:
                    user = User.objects.create_user(
                        email='accountant@test.com',
                        password='password123',
                        tenant=tenant,
                        first_name='Test',
                        last_name='Accountant'
                    )
                    self.stdout.write(f"Created user: {user.email}")

                # 3. Setup Chart of Accounts
                self.stdout.write("Setting up Chart of Accounts...")
                coa_data = [
                    ('1000', 'Cash at Bank', 'asset_current', True),
                    ('1100', 'Accounts Receivable', 'asset_current', False),
                    ('4000', 'Sales Revenue', 'revenue', False),
                    ('5000', 'Cost of Sales', 'cost_of_sales', False),
                    ('6000', 'Operating Expenses', 'expense', False),
                ]
                
                accounts = {}
                for code, name, acc_type, is_bank in coa_data:
                    acc, _ = ChartOfAccount.objects.update_or_create(
                        tenant=tenant, account_code=code,
                        defaults={'account_name': name, 'account_type': acc_type, 'is_bank_account': is_bank}
                    )
                    accounts[code] = acc

                # 4. Setup Integration Rules
                self.stdout.write("Configuring Integration Rules...")
                rules = [
                    ('payment_received', accounts['1000'], accounts['1100']), # Dr Bank, Cr AR
                    ('pos_sale', accounts['1000'], accounts['4000']),       # Dr Cash/Bank, Cr Revenue
                ]
                
                for event, dr, cr in rules:
                    AccountingIntegration.objects.update_or_create(
                        tenant=tenant, event_type=event,
                        defaults={'debit_account': dr, 'credit_account': cr, 'is_active': True}
                    )

                # 5. Create Billing Transaction
                self.stdout.write("Simulating Billing Transaction...")
                tier, _ = PlanTier.objects.get_or_create(tenant=tenant, name='Standard', slug='standard')
                plan, _ = Plan.objects.get_or_create(
                    tenant=tenant, name='Pro Monthly', 
                    defaults={'price': 500, 'plan_tier': tier, 'currency': 'USD'}
                )
                sub, _ = Subscription.objects.get_or_create(
                    tenant=tenant, user=user, subscription_plan=plan,
                    defaults={'status': 'active', 'start_date': timezone.now()}
                )
                
                inv = Invoice.objects.create(
                    tenant=tenant, subscription=sub, 
                    amount=500, status='open', 
                    invoice_number=f"INV-{timezone.now().timestamp()}",
                    due_date=timezone.now().date()
                )
                
                # Payment triggers the signal
                pay = Payment.objects.create(
                    tenant=tenant, invoice=inv, amount=500, 
                    status='succeeded', payment_method_id=1,
                    processed_at=timezone.now()
                )
                self.stdout.write(f"Payment created: {pay.id}")

                # 6. Create POS Transaction
                self.stdout.write("Simulating POS Transaction...")
                warehouse, _ = Warehouse.objects.get_or_create(
                    tenant=tenant, name='Main Store', 
                    defaults={'code': 'MAIN'}
                )
                terminal, _ = POSTerminal.objects.get_or_create(
                    terminal_code='T001',
                    defaults={'terminal_name': 'Front Counter', 'tenant': tenant, 'warehouse': warehouse}
                )
                
                pos_trans = POSTransaction.objects.create(
                    tenant=tenant, terminal=terminal, user=user,
                    status='completed', total_amount=150,
                    transaction_number=f"POS-{timezone.now().timestamp()}"
                )
                
                # POS Payment might trigger signal depending on implementation
                POSPayment.objects.create(
                    tenant=tenant, transaction=pos_trans,
                    amount=150, method='cash', status='completed'
                )
                self.stdout.write(f"POS Transaction created: {pos_trans.transaction_number}")

                # 7. Final Verification
                self.stdout.write("\nVerification Results:")
                journals = JournalEntry.objects.filter(tenant=tenant)
                self.stdout.write(f"Total Journal Entries: {journals.count()}")
                for j in journals:
                    self.stdout.write(f"[{j.entry_number}] {j.description} - Status: {j.status}")
                    for line in j.lines.all():
                        self.stdout.write(f"  {line.account.account_name}: Dr {line.debit} | Cr {line.credit}")
                
                # Check Bank Balance
                bank = accounts['1000']
                bank.refresh_from_db()
                self.stdout.write(f"\nFinal Bank Balance: {bank.current_balance}")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error seeding data: {e}"))
            import traceback
            traceback.print_exc()

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
