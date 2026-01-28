from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from .models import JournalEntry, JournalEntryLine, ChartOfAccount, FiscalPeriod, BankReconciliation

class JournalService:
    @staticmethod
    def create_journal_entry(
        tenant,
        date,
        description,
        user,
        lines,
        reference='',
        status='draft',
        related_object=None
    ):
        """
        Create a journal entry with validation.
        lines: List of dicts {'account': obj, 'debit': decimal, 'credit': decimal, 'description': str}
        """
        # Validate balance
        total_debit = sum(line['debit'] for line in lines)
        total_credit = sum(line['credit'] for line in lines)
        
        if total_debit != total_credit:
            raise ValueError(f"Journal Entry is not balanced. Debit: {total_debit}, Credit: {total_credit}")
            
        # Create Header
        journal = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date,
            description=description,
            created_by=user,
            reference=reference,
            status='draft' # Always start as draft unless auto-posting is checked
        )
        
        # Create Lines
        for line_data in lines:
            JournalEntryLine.objects.create(
                tenant=tenant,
                journal_entry=journal,
                account=line_data['account'],
                description=line_data.get('description', ''),
                debit=line_data['debit'],
                credit=line_data['credit'],
                # Add partner_id if available (not in current model structure but good for future)
            )
            
        if status == 'posted':
            JournalService.post_journal_entry(journal, user)
            
        return journal

    @staticmethod
    def post_journal_entry(journal, user):
        """
        Post a journal entry: Lock it and update account balances.
        """
        if journal.status == 'posted':
            return
            
        if not journal.is_balanced:
             raise ValueError("Cannot post unbalanced journal.")
             
        journal.status = 'posted'
        journal.posted_by = user
        journal.posted_at = timezone.now()
        journal.save()
        
        # Update Balances
        for line in journal.lines.all():
            account = line.account
            # Standard Accounting Equation Updates
            # Asset/Expense: Dr + / Cr -
            # Liability/Equity/Income: Cr + / Dr -
            
            if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                account.current_balance += (line.debit - line.credit)
            else:
                account.current_balance += (line.credit - line.debit)
            
            account.save()

class ReportService:
    @staticmethod
    def get_trial_balance(tenant, as_of_date):
        accounts = ChartOfAccount.objects.filter(tenant=tenant).order_by('account_code')
        report_data = []
        total_debit = Decimal(0)
        total_credit = Decimal(0)

        for account in accounts:
            balance = account.current_balance # Optimization: Use stored balance if rebuilt correctly
            # Or recalculate from lines for accuracy at historical date
            
            if as_of_date < timezone.now().date():
                # Must calculate historical balance
                # This is expensive, better to have periodic snapshots
                # For now, simple aggregation
                qs = JournalEntryLine.objects.filter(
                    tenant=tenant,
                    account=account,
                    journal_entry__status='posted',
                    journal_entry__entry_date__lte=as_of_date
                )
                res = qs.aggregate(d=Sum('debit'), c=Sum('credit'))
                debit_sum = res['d'] or Decimal(0)
                credit_sum = res['c'] or Decimal(0)
                
                if account.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    net = debit_sum - credit_sum
                else:
                    net = credit_sum - debit_sum
            else:
                net = account.current_balance

            if net != 0:
                report_data.append({
                    'code': account.account_code,
                    'name': account.account_name,
                    'balance': net,
                    'type': account.account_type
                })
                
                # For TB columns
                if net > 0:
                     if account.account_type in ['asset', 'expense']: # Normal Debit
                         total_debit += net
                     else:
                         total_credit += net # Normal Credit
                else:
                    # Negative balance means contra-normal
                    pass # Handle complexity
                    
        return report_data

    @staticmethod
    def get_balance_sheet(tenant, as_of_date):
        # IFRS Structure: Assets (Non-current, Current), Equity, Liabilities (Non-current, Current)
        
        def get_total(types):
             accounts = ChartOfAccount.objects.filter(tenant=tenant, account_type__in=types)
             total = Decimal(0)
             details = []
             for acc in accounts:
                 # Logic to get balance at date similar to Trial Balance
                 # ... simplified for brevity using current_balance
                 bal = acc.current_balance 
                 if bal != 0:
                     details.append({'name': acc.account_name, 'amount': bal})
                     total += bal
             return total, details

        assets_nc_total, assets_nc = get_total(['asset_non_current'])
        assets_c_total, assets_c = get_total(['asset_current', 'asset']) # Fallback for legacy 'asset'
        
        equity_total, equity = get_total(['equity'])
        
        liab_nc_total, liab_nc = get_total(['liability_non_current'])
        liab_c_total, liab_c = get_total(['liability_current', 'liability'])

        
        # Retained Earnings Calculation (Revenue - Expense)
        # In a real system, this is closed to Retained Earnings account at year end.
        # If not closed, calculate on fly.
        
        return {
            'assets': {'current': assets_c, 'non_current': assets_nc, 'total': assets_c_total + assets_nc_total},
            'equity': {'details': equity, 'total': equity_total},
            'liabilities': {'current': liab_c, 'non_current': liab_nc, 'total': liab_c_total + liab_nc_total}
        }
