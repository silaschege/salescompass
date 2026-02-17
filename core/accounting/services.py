from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from .models import (
    JournalEntry, JournalEntryLine, ChartOfAccount, 
    FiscalPeriod, BankReconciliation, FiscalYear,
    Currency, ExchangeRate
)

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
        currency=None,
        exchange_rate=None,
        related_object=None
    ):
        """
        Create a journal entry with validation.
        lines: List of dicts {'account': obj, 'debit': decimal, 'credit': decimal, 'description': str}
        """
        # Multi-currency handling
        if not currency:
            # Default to 1.0 if no currency specified
            exchange_rate = Decimal('1.0')
        elif not exchange_rate:
            # Try to fetch latest rate
            exchange_rate = JournalService.get_exchange_rate(tenant, currency, date)

        # Validate balance in transaction currency
        total_debit_curr = sum(Decimal(str(line.get('debit', 0))) for line in lines)
        total_credit_curr = sum(Decimal(str(line.get('credit', 0))) for line in lines)
        
        if total_debit_curr != total_credit_curr:
            raise ValueError(f"Journal Entry is not balanced. Debit: {total_debit_curr}, Credit: {total_credit_curr}")
            
        # Create Header
        journal = JournalEntry.objects.create(
            tenant=tenant,
            entry_date=date,
            description=description,
            created_by=user,
            reference=reference,
            currency=currency,
            exchange_rate=exchange_rate,
            status='draft'
        )
        
        # Create Lines
        for line_data in lines:
            amt_debit = Decimal(str(line_data.get('debit', 0)))
            amt_credit = Decimal(str(line_data.get('credit', 0)))
            
            # Convert to base currency
            base_debit = (amt_debit * exchange_rate).quantize(Decimal('0.01'))
            base_credit = (amt_credit * exchange_rate).quantize(Decimal('0.01'))

            JournalEntryLine.objects.create(
                tenant=tenant,
                journal_entry=journal,
                account=line_data['account'],
                description=line_data.get('description', ''),
                debit_currency=amt_debit,
                credit_currency=amt_credit,
                debit=base_debit,
                credit=base_credit,
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

    @staticmethod
    def get_exchange_rate(tenant, currency, date=None):
        """
        Helper to get exchange rate for a currency against the tenant's base currency.
        Base currency is assumed to be the 'target' of the rate (1 currency = X base).
        """
        if not date:
            date = timezone.now().date()
            
        rate_obj = ExchangeRate.objects.filter(
            tenant=tenant,
            from_currency=currency,
            date__lte=date
        ).order_by('-date').first()
        
        if rate_obj:
            return rate_obj.rate
            
        return Decimal('1.0') # Default fallback

class ReportService:
    @staticmethod
    def get_trial_balance(tenant, as_of_date):
        """
        Calculates the Trial Balance for a given date.
        Returns a dictionary containing report_data (list of accounts), 
        total_debit, and total_credit.
        """
        accounts = ChartOfAccount.objects.filter(tenant=tenant).order_by('account_code')
        report_data = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for account in accounts:
            qs = JournalEntryLine.objects.filter(
                tenant=tenant,
                account=account,
                journal_entry__status='posted',
                journal_entry__entry_date__lte=as_of_date
            )
            res = qs.aggregate(d=Sum('debit'), c=Sum('credit'))
            debit_sum = res['d'] or Decimal('0.00')
            credit_sum = res['c'] or Decimal('0.00')
            
            if debit_sum != 0 or credit_sum != 0:
                report_data.append({
                    'code': account.account_code,
                    'name': account.account_name,
                    'debit': debit_sum,
                    'credit': credit_sum,
                    'type': account.account_type
                })
                total_debit += debit_sum
                total_credit += credit_sum
                    
        return {
            'report_data': report_data,
            'total_debit': total_debit,
            'total_credit': total_credit
        }

    @staticmethod
    def get_income_statement(tenant, start_date, end_date):
        """
        Calculates the Income Statement (P&L) for a period.
        """
        # Revenue
        revenues = ChartOfAccount.objects.filter(tenant=tenant, account_type='revenue')
        revenue_details = []
        total_revenue = Decimal('0.00')
        
        for acc in revenues:
            bal = JournalEntryLine.objects.filter(
                tenant=tenant, account=acc,
                journal_entry__status='posted',
                journal_entry__entry_date__range=(start_date, end_date)
            ).aggregate(d=Sum('debit'), c=Sum('credit'))
            net = (bal['c'] or 0) - (bal['d'] or 0)
            if net != 0:
                revenue_details.append({'name': acc.account_name, 'amount': net})
                total_revenue += net

        # Cost of Sales
        cogs = ChartOfAccount.objects.filter(tenant=tenant, account_type='cost_of_sales')
        cogs_details = []
        total_cogs = Decimal('0.00')
        
        for acc in cogs:
            bal = JournalEntryLine.objects.filter(
                tenant=tenant, account=acc,
                journal_entry__status='posted',
                journal_entry__entry_date__range=(start_date, end_date)
            ).aggregate(d=Sum('debit'), c=Sum('credit'))
            net = (bal['d'] or 0) - (bal['c'] or 0)
            if net != 0:
                cogs_details.append({'name': acc.account_name, 'amount': net})
                total_cogs += net

        gross_profit = total_revenue - total_cogs
        
        # Operating Expenses
        expenses = ChartOfAccount.objects.filter(tenant=tenant, account_type__in=['expense', 'other_expense'])
        expense_details = []
        total_expense = Decimal('0.00')
        
        for acc in expenses:
            bal = JournalEntryLine.objects.filter(
                tenant=tenant, account=acc,
                journal_entry__status='posted',
                journal_entry__entry_date__range=(start_date, end_date)
            ).aggregate(d=Sum('debit'), c=Sum('credit'))
            net = (bal['d'] or 0) - (bal['c'] or 0)
            if net != 0:
                expense_details.append({'name': acc.account_name, 'amount': net})
                total_expense += net
        
        net_income = gross_profit - total_expense
        
        return {
            'revenues': revenue_details,
            'total_revenue': total_revenue,
            'cogs': cogs_details,
            'total_cogs': total_cogs,
            'gross_profit': gross_profit,
            'expenses': expense_details,
            'total_expense': total_expense,
            'net_income': net_income
        }

    @staticmethod
    def get_balance_sheet(tenant, as_of_date):
        """
        Calculates the Balance Sheet as of a specific date.
        """
        def get_net_balance(types, as_of_date):
             accounts = ChartOfAccount.objects.filter(tenant=tenant, account_type__in=types)
             total = Decimal('0.00')
             details = []
             for acc in accounts:
                 res = JournalEntryLine.objects.filter(
                     tenant=tenant, account=acc,
                     journal_entry__status='posted',
                     journal_entry__entry_date__lte=as_of_date
                 ).aggregate(d=Sum('debit'), c=Sum('credit'))
                 
                 d = res['d'] or Decimal('0.00')
                 c = res['c'] or Decimal('0.00')
                 
                 if acc.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                     net = d - c
                 else:
                     net = c - d
                     
                 if net != 0:
                     details.append({'name': acc.account_name, 'amount': net})
                     total += net
             return total, details

        assets_nc_total, assets_nc = get_net_balance(['asset_non_current'], as_of_date)
        assets_c_total, assets_c = get_net_balance(['asset_current', 'asset'], as_of_date)
        
        equity_total, equity = get_net_balance(['equity'], as_of_date)
        
        liab_nc_total, liab_nc = get_net_balance(['liability_non_current'], as_of_date)
        liab_c_total, liab_c = get_net_balance(['liability_current', 'liability'], as_of_date)

        # Calculate Year-to-Date Net Income if not yet closed to Retained Earnings
        # We need the start of the current fiscal year
        fiscal_year = FiscalYear.objects.filter(
            tenant=tenant, 
            start_date__lte=as_of_date, 
            end_date__gte=as_of_date
        ).first()
        
        ytd_net_income = Decimal('0.00')
        if fiscal_year:
            income_data = ReportService.get_income_statement(tenant, fiscal_year.start_date, as_of_date)
            ytd_net_income = income_data['net_income']
            equity.append({'name': 'Net Income (Loss) - Current Period', 'amount': ytd_net_income})
            equity_total += ytd_net_income

        total_assets = assets_c_total + assets_nc_total
        total_liabilities = liab_c_total + liab_nc_total
        
        return {
            'assets': {
                'current': assets_c, 
                'non_current': assets_nc, 
                'current_total': assets_c_total,
                'non_current_total': assets_nc_total,
                'total': total_assets
            },
            'equity': {'details': equity, 'total': equity_total},
            'liabilities': {
                'current': liab_c, 
                'non_current': liab_nc, 
                'current_total': liab_c_total,
                'non_current_total': liab_nc_total,
                'total': total_liabilities
            },
            'total_liabilities_equity': equity_total + total_liabilities
        }

    @staticmethod
    def get_cash_flow_statement(tenant, start_date, end_date):
        """
        Simplified Cash Flow Statement (Direct Method).
        Categorizes transactions to bank/cash accounts.
        """
        cash_accounts = ChartOfAccount.objects.filter(tenant=tenant, is_bank_account=True)
        
        inflows = []
        outflows = []
        total_inflow = Decimal('0.00')
        total_outflow = Decimal('0.00')
        
        for acc in cash_accounts:
            lines = JournalEntryLine.objects.filter(
                tenant=tenant,
                account=acc,
                journal_entry__status='posted',
                journal_entry__entry_date__range=(start_date, end_date)
            )
            
            # For cash accounts (Assets): Dr is inflow, Cr is outflow
            res = lines.aggregate(d=Sum('debit'), c=Sum('credit'))
            d = res['d'] or Decimal('0.00')
            c = res['c'] or Decimal('0.00')
            
            if d > 0:
                inflows.append({'name': acc.account_name, 'amount': d})
                total_inflow += d
            if c > 0:
                outflows.append({'name': acc.account_name, 'amount': c})
                total_outflow += c
                
        return {
            'inflows': inflows,
            'total_inflow': total_inflow,
            'outflows': outflows,
            'total_outflow': total_outflow,
            'net_cash_flow': total_inflow - total_outflow
        }

    @staticmethod
    def get_custom_report(tenant, report_config, as_of_date):
        """
        Generates data for a CustomFinancialReport based on its JSON config.
        Expected config structure: 
        {
            "sections": [
                {
                    "name": "Cash and Equivalents",
                    "account_codes": ["1000", "1010", "1020"]
                },
                {
                    "name": "Accounts Receivable",
                    "account_range": ["1100", "1199"]
                }
            ]
        }
        """
        results = []
        sections = report_config.config_data.get('sections', [])
        
        for section in sections:
            section_name = section.get('name', 'Unnamed Section')
            account_codes = section.get('account_codes', [])
            account_range = section.get('account_range', [])
            
            # Build filter
            account_filter = Q(tenant=tenant)
            if account_codes:
                account_filter &= Q(account_code__in=account_codes)
            elif account_range and len(account_range) == 2:
                account_filter &= Q(account_code__range=(account_range[0], account_range[1]))
            
            accounts = ChartOfAccount.objects.filter(account_filter)
            section_total = Decimal('0.00')
            account_data = []
            
            for acc in accounts:
                # Calculate balance as of date
                res = JournalEntryLine.objects.filter(
                    tenant=tenant, account=acc,
                    journal_entry__status='posted',
                    journal_entry__entry_date__lte=as_of_date
                ).aggregate(d=Sum('debit'), c=Sum('credit'))
                
                d = res['d'] or Decimal('0.00')
                c = res['c'] or Decimal('0.00')
                
                # Default logic: Assets/Expenses are Dr+, others are Cr+
                if acc.account_type in ['asset', 'asset_current', 'asset_non_current', 'expense', 'cost_of_sales', 'other_expense']:
                    balance = d - c
                else:
                    balance = c - d
                
                if balance != 0:
                    account_data.append({'name': acc.account_name, 'code': acc.account_code, 'balance': balance})
                    section_total += balance
            
            results.append({
                'section_name': section_name,
                'accounts': account_data,
                'total': section_total
            })
            
        return results

    @staticmethod
    def get_vat_return(tenant, start_date, end_date):
        """
        Calculates VAT Return: Output VAT (Sales) vs Input VAT (Purchases).
        """
        from .models import TaxRate, JournalEntryLine
        from decimal import Decimal
        from django.db.models import Sum
        
        tax_rates = TaxRate.objects.filter(tenant=tenant, is_active=True)
        report_lines = []
        total_input_vat = Decimal('0.00')
        total_output_vat = Decimal('0.00')
        
        for rate in tax_rates:
            if not rate.account:
                continue
                
            # Get all lines for this account in the period
            lines = JournalEntryLine.objects.filter(
                tenant=tenant,
                account=rate.account,
                journal_entry__status='posted',
                journal_entry__entry_date__range=(start_date, end_date)
            )
            
            # Sum debits and credits
            # Dr is usually Input VAT (Receivable), Cr is Output VAT (Payable)
            res = lines.aggregate(d=Sum('debit'), c=Sum('credit'))
            debit_sum = res['d'] or Decimal('0.00')
            credit_sum = res['c'] or Decimal('0.00')
            
            if debit_sum != 0 or credit_sum != 0:
                report_lines.append({
                    'tax_name': rate.name,
                    'account_name': rate.account.account_name,
                    'input_vat': debit_sum,
                    'output_vat': credit_sum,
                    'net': credit_sum - debit_sum
                })
                total_input_vat += debit_sum
                total_output_vat += credit_sum
                
        return {
            'report_lines': report_lines,
            'total_input_vat': total_input_vat,
            'total_output_vat': total_output_vat,
            'net_vat_due': total_output_vat - total_input_vat
        }

import csv
import io
from .models import BankStatement, BankStatementLine

class BankService:
    @staticmethod
    def parse_csv(file_obj):
        """
        Simple CSV parser. Expects headers: Date, Description, Amount[, Reference]
        Amount: Positive for deposits (Dr to Bank), Negative for withdrawals (Cr to Bank)
        """
        lines = []
        decoded_file = file_obj.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        from django.utils.dateparse import parse_date
        from decimal import Decimal
        
        for row in reader:
            date_val = parse_date(row.get('Date'))
            if not date_val:
                # Try common formats if ISO fails
                try:
                    from datetime import datetime
                    date_val = datetime.strptime(row.get('Date'), '%d/%m/%Y').date()
                except:
                    continue
            
            lines.append({
                'date': date_val,
                'description': row.get('Description', ''),
                'amount': Decimal(row.get('Amount', '0')),
                'reference': row.get('Reference', '')
            })
        return lines

    @staticmethod
    def import_statement(tenant, account, file_obj, filename):
        """
        Import lines from a file object.
        """
        # For now only CSV
        lines_data = BankService.parse_csv(file_obj)
        
        if not lines_data:
            return None
            
        statement = BankStatement.objects.create(
            tenant=tenant,
            account=account,
            file_name=filename,
            start_date=min(l['date'] for l in lines_data),
            end_date=max(l['date'] for l in lines_data)
        )
        
        for line_data in lines_data:
            BankStatementLine.objects.create(
                tenant=tenant,
                statement=statement,
                **line_data
            )
            
        return statement

    @staticmethod
    def suggest_matches(bank_line):
        """
        Suggest matching JournalEntryLines for a BankStatementLine.
        Logic: 
        - Same account (already filtered by statement)
        - Same amount (Bank Dr = JE Dr, Bank Cr = JE Cr)
        - Date within +/- 7 days
        """
        from .models import JournalEntryLine
        
        amount = abs(bank_line.amount)
        is_deposit = bank_line.amount > 0
        
        # A deposit in bank means we should have a Journal Entry debiting the Bank account
        # A withdrawal from bank means we should have a Journal Entry crediting the Bank account
        
        queryset = JournalEntryLine.objects.filter(
            tenant=bank_line.tenant,
            account=bank_line.statement.account,
            is_reconciled=False,
            journal_entry__status='posted'
        )
        
        if is_deposit:
            queryset = queryset.filter(debit=amount)
        else:
            queryset = queryset.filter(credit=amount)
            
        # Date proximity
        from datetime import timedelta
        start_date = bank_line.date - timedelta(days=7)
        end_date = bank_line.date + timedelta(days=7)
        
        queryset = queryset.filter(journal_entry__entry_date__range=(start_date, end_date))
        
        return queryset

    @staticmethod
    def reconcile(bank_line, journal_line):
        """
        Link a bank statement line with a journal entry line.
        """
        if bank_line.is_reconciled or journal_line.is_reconciled:
            raise ValueError("One of the lines is already reconciled.")
            
        # Additional validation could go here (e.g. amount match)
        
        bank_line.reconciled_line = journal_line
        bank_line.is_reconciled = True
        bank_line.save()
        
        journal_line.is_reconciled = True
        journal_line.save()
        
        return True

        return True

    @staticmethod
    def fetch_api_transactions(tenant, api_config):
        """
        Mock implementation of fetching transactions from a bank API.
        """
        import random
        from datetime import date, timedelta
        
        # In a real implementation, we would use api_config.credentials_json
        # and a library for Plaid/Tink/etc.
        
        if api_config.provider == 'mock':
            mock_transactions = []
            today = timezone.now().date()
            
            # Generate 5 random transactions for the last 7 days
            for i in range(5):
                days_ago = random.randint(0, 7)
                tx_date = today - timedelta(days=days_ago)
                amount = Decimal(str(random.uniform(-500.0, 500.0))).quantize(Decimal('0.01'))
                description = random.choice(['Starbucks', 'Office Depot', 'Client Payment', 'Rent', 'Internet'])
                
                mock_transactions.append({
                    'date': tx_date,
                    'description': f"Bank API: {description}",
                    'amount': amount,
                    'reference': f"API-{random.randint(1000, 9999)}"
                })
                
            # Create a BankStatement for this sync
            statement = BankStatement.objects.create(
                tenant=tenant,
                account=api_config.account,
                file_name=f"API_SYNC_{api_config.provider}_{today}",
                start_date=min(t['date'] for t in mock_transactions),
                end_date=max(t['date'] for t in mock_transactions)
            )
            
            for tx in mock_transactions:
                BankStatementLine.objects.create(
                    tenant=tenant,
                    statement=statement,
                    **tx
                )
                
            api_config.last_sync = timezone.now()
            api_config.save()
            
            return statement
            
        return None
