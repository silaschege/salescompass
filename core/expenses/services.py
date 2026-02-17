from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from accounting.models import AccountingIntegration, ChartOfAccount
from accounting.services import JournalService
from assets.models import FixedAsset, AssetCategory
from .models import ExpenseReport, ExpenseLine

class ExpenseAccountingService:
    """
    Service to handle IFRS/IPSAS compliant accounting for expenses.
    """

    @staticmethod
    @transaction.atomic
    def post_accrual(report, user):
        """
        Recognize expense accrual upon approval.
        Dr Expense (from Category)
        Cr Accrued Liability (Accruals)
        """
        if report.is_accrued:
            return None

        tenant = report.tenant
        lines_to_post = []
        
        # Get integration rule for accrual
        try:
            accrual_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='expense_accrual',
                is_active=True
            )
            liability_account = accrual_rule.credit_account
        except AccountingIntegration.DoesNotExist:
            # Fallback: Find a "Payables" or "Accrued" account
            liability_account = ChartOfAccount.objects.filter(
                tenant=tenant,
                account_type='liability_current',
                account_name__icontains='Accrued'
            ).first()

        if not liability_account:
             raise ValueError("No accrual liability account configured for expenses.")

        # Aggregate report lines by their category's GL account
        journal_lines = []
        total_amount = Decimal('0.00')

        for line in report.lines.all():
            expense_account = line.category.gl_account
            if not expense_account:
                continue
                
            journal_lines.append({
                'account': expense_account,
                'debit': line.amount - line.tax_amount,
                'credit': Decimal('0.00'),
                'description': f"Exp: {line.description} (Report {report.report_number})"
            })
            
            # Handle Tax (VAT) portion if any
            if line.tax_amount > 0:
                # Find Tax account... assuming a generic current asset/liability for now
                # Or a specific tax integration? 
                pass # Logic for tax splitting could go here

            total_amount += line.amount

            # Trigger CAPEX conversion if needed
            if line.is_capex:
                 ExpenseAccountingService.convert_to_asset(line, user)

        if not journal_lines:
            return None

        # Add the Credit leg
        journal_lines.append({
            'account': liability_account,
            'debit': Decimal('0.00'),
            'credit': total_amount,
            'description': f"Accrual for Expense Report {report.report_number}"
        })

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Accrual for Expense Report: {report.title}",
            user=user,
            lines=journal_lines,
            reference=report.report_number,
            status='posted',
            related_object=report
        )
        
        report.is_accrued = True
        report.save()
        return journal

    @staticmethod
    @transaction.atomic
    def post_payment(report, user):
        """
        Recognize payment/reimbursement.
        Dr Accrued Liability
        Cr Cash/Bank
        """
        tenant = report.tenant
        
        # Get integration rule for payment
        try:
            payment_rule = AccountingIntegration.objects.get(
                tenant=tenant,
                event_type='expense_payment',
                is_active=True
            )
            bank_account = payment_rule.credit_account # Usually CR Bank/Cash
            liability_account = payment_rule.debit_account # Usually DR Accrued Liability
        except AccountingIntegration.DoesNotExist:
             raise ValueError("No payment integration rule configured for expenses.")

        journal_lines = [
            {
                'account': liability_account,
                'debit': report.total_amount,
                'credit': Decimal('0.00'),
                'description': f"Payment Settlement (Report {report.report_number})"
            },
            {
                'account': bank_account,
                'debit': Decimal('0.00'),
                'credit': report.total_amount,
                'description': f"Payment Settlement (Report {report.report_number})"
            }
        ]

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=timezone.now().date(),
            description=f"Payment/Reimbursement for Expense Report: {report.title}",
            user=user,
            lines=journal_lines,
            reference=report.report_number,
            status='posted',
            related_object=report
        )
        
        return journal

    @staticmethod
    def convert_to_asset(line, user):
        """
        Converts a CAPEX expense line to a FixedAsset.
        """
        # Find or create a matching asset category
        asset_cat = AssetCategory.objects.filter(tenant=line.tenant, name=line.category.name).first()
        if not asset_cat:
            # Fallback to first available or create general
            asset_cat = AssetCategory.objects.filter(tenant=line.tenant).first()
            
        if not asset_cat:
            return None # No asset categories setup
            
        import uuid
        asset = FixedAsset.objects.create(
            tenant=line.tenant,
            asset_number=f"AST-{uuid.uuid4().hex[:8].upper()}",
            name=line.description,
            category=asset_cat,
            purchase_date=line.date,
            purchase_cost=line.amount,
            status='active',
            assigned_to=line.report.employee
        )
        
        line.related_asset = asset
        line.save()
        return asset


class PolicyService:
    """
    Service to enforce expense policies.
    """
    @staticmethod
    def validate_line(line):
        """
        Validates a single expense line against active policies.
        Returns a list of violation messages.
        """
        violations = []
        tenant = line.tenant
        
        # 1. Fetch relevant policies (Global or Category-specific)
        from .models import ExpensePolicy
        policies = ExpensePolicy.objects.filter(
            tenant=tenant,
            is_active=True
        ).filter(
            models.Q(category=line.category) | models.Q(category__isnull=True)
        )
        
        for policy in policies:
            # Check transaction limit
            if policy.max_amount_per_transaction and line.amount > policy.max_amount_per_transaction:
                msg = f"Amount {line.amount} exceeds limit of {policy.max_amount_per_transaction} for {policy}"
                violations.append({'message': msg, 'action': policy.action_on_violation})
                
            # Check daily limit (requires aggregation, maybe expensive for every line save?)
            # Optimization: Only check if policy has daily limit
            if policy.max_amount_daily:
                today_total = ExpenseLine.objects.filter(
                    report__employee=line.report.employee,
                    date=line.date,
                    report__tenant=tenant
                ).aggregate(sum=models.Sum('amount'))['sum'] or 0
                
                # Add current line amount if not already saved/included (this is tricky during validation before save)
                # Assuming this is called before save, we add current amount. 
                # If called after, we don't.
                # Let's assume pre-save check usage.
                if not line.pk:
                    today_total += line.amount
                    
                if today_total > policy.max_amount_daily:
                    msg = f"Daily total {today_total} exceeds limit of {policy.max_amount_daily}"
                    violations.append({'message': msg, 'action': policy.action_on_violation})

        return violations

    @staticmethod
    def check_report_policies(report):
        """
        Checks all lines in a report for policy violations.
        Returns (is_blocked, warnings_list)
        """
        warnings = []
        is_blocked = False
        
        for line in report.lines.all():
            violations = PolicyService.validate_line(line)
            for v in violations:
                warnings.append(v['message'])
                if v['action'] == 'block':
                    is_blocked = True
                    
        return is_blocked, warnings


class ApprovalService:
    """
    Service to handle multi-level approval workflows.
    """
    @staticmethod
    def submit_report(report, user):
        """
        Handles the initial submission of a report.
        Assigns the appropriate workflow and first step.
        """
        from .models import ExpenseApprovalWorkflow
        
        # 1. Determine Workflow
        # For now, pick the first active one or a default
        workflow = ExpenseApprovalWorkflow.objects.filter(tenant=report.tenant, is_active=True).first()
        
        if not workflow:
            # Fallback to legacy single-step behavior
            report.status = 'submitted'
            report.submitted_date = timezone.now()
            report.save()
            return report
            
        report.approval_workflow = workflow
        
        # 2. Determine First Step
        steps = workflow.steps.order_by('step_order')
        first_step = None
        
        for step in steps:
            # Check conditions (e.g. min_amount)
            if report.total_amount >= step.min_amount:
                first_step = step
                break
        
        if first_step:
            report.status = 'pending_approval' # New status for workflow
            report.current_step = first_step
            report.submitted_date = timezone.now()
            report.save()
            # Notify approver?
        else:
            # No applicable steps (maybe below threshold?)
            # Auto-approve? Or consider Submitted?
            # Let's auto-approve if no steps apply but workflow exists
            report.status = 'approved' 
            report.submitted_date = timezone.now()
            report.approved_date = timezone.now()
            report.save()
             # Trigger Accounting
            ExpenseAccountingService.post_accrual(report, user)
            
        return report

    @staticmethod
    def approve_step(report, user):
        """
        Approves the current step and moves to the next.
        """
        current_step = report.current_step
        if not current_step:
            # Legacy or error state
            if report.status == 'submitted':
                 # Finalize legacy approval
                 report.status = 'approved'
                 report.approved_by = user
                 report.approved_date = timezone.now()
                 report.save()
                 ExpenseAccountingService.post_accrual(report, user)
            return

        workflow = report.approval_workflow
        
        # Find next step
        next_step = workflow.steps.filter(
            step_order__gt=current_step.step_order,
            min_amount__lte=report.total_amount
        ).order_by('step_order').first()
        
        if next_step:
            report.current_step = next_step
            report.save()
             # Notify next approver?
        else:
            # End of workflow -> Fully Approved
            report.status = 'approved'
            report.current_step = None
            report.approved_by = user # Record final approver
            report.approved_date = timezone.now()
            report.save()
            
            # Trigger Accounting
            ExpenseAccountingService.post_accrual(report, user)

    @staticmethod
    def reject_report(report, user, reason):
        report.status = 'rejected'
        report.rejection_reason = reason
        report.current_step = None # Reset workflow step
        report.save()


class CardImportService:
    """
    Service to import and manage corporate card transactions.
    """
    @staticmethod
    def import_transactions_csv(csv_file, card):
        """
        Parses a CSV file and creates CardTransaction records.
        Expected format: Date, Merchant, Amount, Currency, Description, Ref
        """
        import csv
        import io
        from datetime import datetime
        from .models import CardTransaction
        
        # Decode file if binary
        if hasattr(csv_file, 'read'):
            csv_file = io.TextIOWrapper(csv_file, encoding='utf-8')
            
        reader = csv.DictReader(csv_file)
        created_count = 0
        
        for row in reader:
            # Basic validation and parsing
            try:
                # Flexible date parsing (try YYYY-MM-DD then DD/MM/YYYY)
                date_str = row.get('Date', '').strip()
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                    
                amount = Decimal(row.get('Amount', '0').replace(',', ''))
                merchant = row.get('Merchant', 'Unknown')
                currency = row.get('Currency', 'KES')
                desc = row.get('Description', '')
                ref = row.get('Ref', '')
                
                # Check duplicate (simple check by ref + date + amount)
                if CardTransaction.objects.filter(
                    card=card, 
                    reference_number=ref, 
                    date=date_obj, 
                    amount=amount
                ).exists():
                    continue

                CardTransaction.objects.create(
                    tenant=card.tenant,
                    card=card,
                    date=date_obj,
                    merchant=merchant,
                    amount=amount,
                    currency=currency,
                    description=desc,
                    reference_number=ref,
                    status='unmatched'
                )
                created_count += 1
                
            except Exception as e:
                # Log error or skip row
                print(f"Error parsing row {row}: {e}")
                continue
                
        return created_count

    @staticmethod
    def auto_match_transactions(tenant):
        """
        Attempts to match Unmatched transactions to ExpenseLines.
        Matching logic: Same Date AND Same Amount.
        """
        from .models import CardTransaction, ExpenseLine
        
        unmatched_txs = CardTransaction.objects.filter(tenant=tenant, status='unmatched')
        matched_count = 0
        
        for tx in unmatched_txs:
            # Find candidate lines: Same date, same amount, no linked transaction
            candidate = ExpenseLine.objects.filter(
                tenant=tenant,
                date=tx.date,
                amount=tx.amount,
                matched_transaction__isnull=True
            ).first()
            
            if candidate:
                candidate.matched_transaction = tx
                candidate.save()
                
                tx.status = 'matched'
                tx.save()
                matched_count += 1
                
        return matched_count


class AnalyticsService:
    """
    Provides data aggregation for expenses dashboard.
    """
    @staticmethod
    def get_spend_by_category(tenant, start_date, end_date):
        return ExpenseLine.objects.filter(
            tenant=tenant,
            report__status__in=['approved', 'paid'],
            date__range=(start_date, end_date)
        ).values('category__name').annotate(total=models.Sum('amount')).order_by('-total')
        
    @staticmethod
    def get_spend_trend(tenant, start_date, end_date):
        # Weekly or Monthly trend
        # For simplicity return daily
        return ExpenseLine.objects.filter(
            tenant=tenant,
            report__status__in=['approved', 'paid'],
            date__range=(start_date, end_date)
        ).values('date').annotate(total=models.Sum('amount')).order_by('date')


class OCRService:
    """
    Service for extracting data from receipt images.
    Connects to Tesseract or Cloud OCR APIs.
    """
    @staticmethod
    def extract_data(image_file):
        """
        Extracts date, amount, merchant from image.
        """
        # Placeholder for Phase 2 MVP
        # In a real implementation, we would use pytesseract here.
        # import pytesseract
        # from PIL import Image
        # text = pytesseract.image_to_string(Image.open(image_file))
        
        # Mock Response
        import random
        return {
            'merchant': 'OCR Detected Merchant',
            'date': timezone.now().date(),
            'amount': Decimal(random.randrange(100, 5000))
        }
