from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from accounting.models import ChartOfAccount, JournalEntry, JournalEntryLine, BankStatement, BankStatementLine, TaxRate
from accounting.services import BankService, ReportService
from decimal import Decimal
import io

class Phase2Test(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Phase 2 Tenant", schema_name="p2")
        self.user = User.objects.create_user(username="p2_user", email="p2@test.com", password="password")
        self.tenant.users.add(self.user)
        
        self.bank_account = ChartOfAccount.objects.create(
            tenant=self.tenant,
            account_code="1000",
            account_name="Bank 1",
            account_type="asset_current",
            is_bank_account=True
        )
        
        self.tax_account = ChartOfAccount.objects.create(
            tenant=self.tenant,
            account_code="2200",
            account_name="VAT Control",
            account_type="liability_current"
        )
        
        self.tax_rate = TaxRate.objects.create(
            tenant=self.tenant,
            name="VAT 15%",
            rate=15,
            account=self.tax_account
        )

    def test_csv_parsing(self):
        csv_content = "Date,Description,Amount,Reference\n2026-01-01,Test Deposit,1000.00,REF1\n2026-01-02,Test Withdrawal,-500.00,REF2"
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        
        statement = BankService.import_statement(self.tenant, self.bank_account, file_obj, "test.csv")
        
        self.assertIsNotNone(statement)
        self.assertEqual(statement.lines.count(), 2)
        deposit = statement.lines.get(amount=1000)
        self.assertEqual(deposit.description, "Test Deposit")
        self.assertEqual(deposit.reference, "REF1")

    def test_suggest_matches(self):
        # Create a posted journal entry
        journal = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_number="JE-MATCH",
            entry_date=timezone.now().date(),
            status='posted'
        )
        je_line = JournalEntryLine.objects.create(
            tenant=self.tenant,
            journal_entry=journal,
            account=self.bank_account,
            debit=Decimal("100.00"),
            credit=Decimal("0.00")
        )
        
        # Create bank statement line
        statement = BankStatement.objects.create(tenant=self.tenant, account=self.bank_account, file_name="test.csv")
        bank_line = BankStatementLine.objects.create(
            tenant=self.tenant,
            statement=statement,
            date=timezone.now().date(),
            amount=Decimal("100.00"),
            description="Bank Deposit"
        )
        
        suggestions = BankService.suggest_matches(bank_line)
        self.assertIn(je_line, suggestions)

    def test_vat_report(self):
        # Create a posted journal entry with tax
        journal = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_number="JE-VAT",
            entry_date=timezone.now().date(),
            status='posted'
        )
        # Sales VAT (Credit)
        JournalEntryLine.objects.create(
            tenant=self.tenant,
            journal_entry=journal,
            account=self.tax_account,
            debit=Decimal("0.00"),
            credit=Decimal("150.00")
        )
        # Purchase VAT (Debit)
        JournalEntryLine.objects.create(
            tenant=self.tenant,
            journal_entry=journal,
            account=self.tax_account,
            debit=Decimal("50.00"),
            credit=Decimal("0.00")
        )
        
        report = ReportService.get_vat_return(self.tenant, timezone.now().date(), timezone.now().date())
        self.assertEqual(report['total_input_vat'], Decimal("50.00"))
        self.assertEqual(report['total_output_vat'], Decimal("150.00"))
        self.assertEqual(report['net_vat_due'], Decimal("100.00"))
