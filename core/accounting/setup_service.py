from .models import ChartOfAccount, AccountingIntegration, TaxRate
from django.db import transaction

class AccountingSetupService:
    """
    Service to initialize default accounting data for a tenant.
    """
    
    DEFAULT_ACCOUNTS = [
        # Assets
        {'code': '1000', 'name': 'Cash on Hand', 'type': 'asset_current', 'is_bank': False},
        {'code': '1010', 'name': 'Bank Account (Primary)', 'type': 'asset_current', 'is_bank': True},
        {'code': '1100', 'name': 'Accounts Receivable', 'type': 'asset_current', 'is_bank': False},
        {'code': '1500', 'name': 'Inventory Asset', 'type': 'asset_current', 'is_bank': False},
        {'code': '1600', 'name': 'Property, Plant & Equipment', 'type': 'asset_non_current', 'is_bank': False},
        
        # Liabilities
        {'code': '2000', 'name': 'Accounts Payable', 'type': 'liability_current'},
        {'code': '2100', 'name': 'Accrued Liabilities', 'type': 'liability_current'},
        {'code': '2200', 'name': 'VAT Payable', 'type': 'liability_current'},
        {'code': '2300', 'name': 'Payroll Liabilities', 'type': 'liability_current'},
        
        # Equity
        {'code': '3000', 'name': 'Owner\'s Equity', 'type': 'equity'},
        {'code': '3100', 'name': 'Retained Earnings', 'type': 'equity'},
        
        # Revenue
        {'code': '4000', 'name': 'Sales Revenue', 'type': 'revenue'},
        {'code': '4100', 'name': 'Service Revenue', 'type': 'revenue'},
        
        # Cost of Sales
        {'code': '5000', 'name': 'Cost of Goods Sold', 'type': 'cost_of_sales'},
        
        # Expenses
        {'code': '6000', 'name': 'General & Administrative', 'type': 'expense'},
        {'code': '6100', 'name': 'Travel & Entertainment', 'type': 'expense'},
        {'code': '6200', 'name': 'Office Supplies', 'type': 'expense'},
        {'code': '6300', 'name': 'Rent Expense', 'type': 'expense'},
        {'code': '6400', 'name': 'Salaries & Wages', 'type': 'expense'},
        {'code': '6500', 'name': 'Marketing Expense', 'type': 'expense'},
    ]

    @staticmethod
    @transaction.atomic
    def setup_tenant(tenant):
        """
        Idempotently sets up the default accounting structure.
        """
        accounts = AccountingSetupService.setup_chart_of_accounts(tenant)
        AccountingSetupService.setup_integrations(tenant, accounts)
        AccountingSetupService.setup_tax(tenant, accounts)
        
        return accounts

    @staticmethod
    def setup_chart_of_accounts(tenant):
        created_accounts = {}
        for acc_data in AccountingSetupService.DEFAULT_ACCOUNTS:
            account, created = ChartOfAccount.objects.get_or_create(
                tenant=tenant,
                account_code=acc_data['code'],
                defaults={
                    'account_name': acc_data['name'],
                    'account_type': acc_data['type'],
                    'is_bank_account': acc_data.get('is_bank', False),
                    'is_active': True
                }
            )
            created_accounts[acc_data['code']] = account
        return created_accounts

    @staticmethod
    def setup_integrations(tenant, accounts):
        """
        Sets up default integration rules.
        """
        # Helper to get account by code (assuming default codes)
        def get_acc(code):
            return accounts.get(code)
            
        # Define Default mappings
        # (Event, Debit Account, Credit Account)
        mappings = [
            # Sales
            ('invoice_validated', '1100', '4000'), # Dr AR, Cr Revenue
            ('payment_received', '1010', '1100'),  # Dr Bank, Cr AR
            
            # Purchasing
            ('bill_approved', '6000', '2000'),    # Dr Expense (Default), Cr AP
            ('grn_received', '1500', '2100'),     # Dr Inventory, Cr Accrued/GRNI (Using Accrued Liab here)
            ('payment_sent', '2000', '1010'),     # Dr AP, Cr Bank
            
            # Expenses
            ('expense_accrual', None, '2100'),    # Dr Category-GL (Dynamic), Cr Accrued Liabilities
            ('expense_payment', '2100', '1010'),  # Dr Accrued Liabilites, Cr Bank
            
            # Payroll
            ('payroll_accrual', '6400', '2300'),  # Dr Salaries Exp, Cr Payroll Liab
            ('payroll_payment', '2300', '1010'),  # Dr Payroll Liab, Cr Bank
        ]
        
        for event, dr_code, cr_code in mappings:
            dr_acc = get_acc(dr_code) if dr_code else None
            cr_acc = get_acc(cr_code) if cr_code else None
            
            # Only create if logic works (some might be dynamic like expense_accrual dictating DR side separately)
            # expenses_accrual needs a credit account mainly.
            
            check_dr = dr_acc or (dr_code is None) # Valid if acc exists OR we expliclty explicitly want None
            check_cr = cr_acc or (cr_code is None)
            
            if check_dr and check_cr:
                AccountingIntegration.objects.get_or_create(
                    tenant=tenant,
                    event_type=event,
                    defaults={
                        'debit_account': dr_acc,
                        'credit_account': cr_acc,
                        'is_active': True
                    }
                )

    @staticmethod
    def setup_tax(tenant, accounts):
        vat_payable = accounts.get('2200')
        if vat_payable:
            TaxRate.objects.get_or_create(
                tenant=tenant,
                name="VAT Standard (16%)",
                defaults={
                    'rate': 16.00,
                    'account': vat_payable,
                    'is_default': True
                }
            )
