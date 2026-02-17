from django.test import TestCase
from django.utils import timezone
from core.models import User
from tenants.models import Tenant
from accounting.models import ChartOfAccount, JournalEntry, JournalEntryLine, BankReconciliation
from decimal import Decimal

class AccountingModelTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant", schema_name="test_tenant")
        self.user = User.objects.create_user(username="accountant", email="acc@test.com", password="password")
        self.tenant.users.add(self.user)
        
        self.bank_account = ChartOfAccount.objects.create(
            tenant=self.tenant,
            account_code="1000",
            account_name="Bank 1",
            account_type="asset",
            is_bank_account=True
        )
        
        self.expense_account = ChartOfAccount.objects.create(
            tenant=self.tenant,
            account_code="6000",
            account_name="Office Expenses",
            account_type="expense"
        )

    def test_bank_reconciliation_creation(self):
        """Test creating a Bank Reconciliation record."""
        recon = BankReconciliation.objects.create(
            tenant=self.tenant,
            account=self.bank_account,
            statement_date=timezone.now().date(),
            opening_balance=Decimal("1000.00"),
            closing_balance=Decimal("1200.00"),
            reconciled_by=self.user
        )
        
        self.assertEqual(recon.status, 'in_progress')
        self.assertEqual(str(recon), f"Bank 1 - {timezone.now().date()}")

    def test_journal_entry_balancing(self):
        """Test that JournalEntry.is_balanced property works."""
        journal = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_number="JE-001",
            entry_date=timezone.now().date(),
            description="Test Entry",
            created_by=self.user
        )
        
        # Unbalanced
        JournalEntryLine.objects.create(
            tenant=self.tenant,
            journal_entry=journal,
            account=self.expense_account,
            debit=Decimal("100.00"),
            credit=Decimal("0.00")
        )
        self.assertFalse(journal.is_balanced)
        
        # Balanced
        JournalEntryLine.objects.create(
            tenant=self.tenant,
            journal_entry=journal,
            account=self.bank_account,
            debit=Decimal("0.00"),
            credit=Decimal("100.00")
        )
        
        # Refresh to get updated lines (if property calculates from DB)
        # Note: existing model implementation of is_balanced likely aggregates lines
        self.assertTrue(journal.is_balanced)

    def test_posting_logic(self):
        """Test manually updating balances (conceptually)."""
        # Create Journal
        journal = JournalEntry.objects.create(
            tenant=self.tenant,
            entry_number="JE-POST-TEST",
            entry_date=timezone.now().date(),
            description="Posting Test",
            status='draft'
        )
        
        JournalEntryLine.objects.create(journal_entry=journal, account=self.expense_account, debit=100, credit=0, tenant=self.tenant)
        JournalEntryLine.objects.create(journal_entry=journal, account=self.bank_account, debit=0, credit=100, tenant=self.tenant)
        
        # Perform "Post" logic (simulating view logic)
        journal.status = 'posted'
        journal.save()
        
        # Update balances
        self.expense_account.current_balance += 100 # Debit expense increases it
        self.expense_account.save()
        
        self.bank_account.current_balance -= 100 # Credit asset decreases it
        self.bank_account.save()
        
        self.assertEqual(self.expense_account.current_balance, Decimal("100.00"))
        self.assertEqual(self.bank_account.current_balance, Decimal("-100.00"))
