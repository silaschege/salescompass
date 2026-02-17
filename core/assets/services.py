from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import FixedAsset, AssetCategory, Depreciation, AssetImpairment, AssetRevaluation, AssetDisposal
from accounting.services import JournalService
from accounting.models import AccountingIntegration, ChartOfAccount, JournalEntry, JournalEntryLine

class AssetDepreciationService:
    """
    Handles complex depreciation calculations and periodic processing.
    """
    
    @staticmethod
    def calculate_period_depreciation(asset, target_date=None):
        """
        Calculates depreciation for a specific period based on method.
        """
        if target_date is None:
            target_date = timezone.now().date()
            
        # Implementation of methods like Straight Line, Declining Balance, Units of Production
        # (Leveraging existing logic but expanding for multi-method support)
        return asset.calculate_depreciation(target_date=target_date)

    @staticmethod
    @transaction.atomic
    def process_monthly_depreciation(tenant, user, target_date=None, unit_data=None):
        """
        Batch process depreciation for all active assets for the current month.
        unit_data: Optional dict {asset_id: current_units} for units_of_production method.
        """
        if target_date is None:
            target_date = timezone.now().date()
            
        assets = FixedAsset.objects.filter(tenant=tenant, status='active')
        
        runs = []
        for asset in assets:
            # Check if already depreciated this month
            if Depreciation.objects.filter(asset=asset, date__month=target_date.month, date__year=target_date.year).exists():
                continue
                
            method = asset.category.depreciation_method
            amount = Decimal('0')
            
            if method == 'straight_line':
                amount = (asset.purchase_cost - asset.salvage_value) / Decimal(str(asset.category.useful_life_years * 12))
            elif method == 'declining_balance':
                rate = Decimal('2.0') / Decimal(str(asset.category.useful_life_years))
                amount = asset.current_value * (rate / Decimal('12'))
            elif method == 'units_of_production':
                if not unit_data or str(asset.id) not in unit_data:
                    continue
                current_units = Decimal(str(unit_data[str(asset.id)]))
                delta_units = current_units - asset.units_consumed_to_date
                if delta_units <= 0:
                    continue
                
                rate_per_unit = (asset.purchase_cost - asset.salvage_value) / asset.total_estimated_units
                amount = rate_per_unit * delta_units
                # Update units consumed
                asset.units_consumed_to_date = current_units
            elif method == 'sum_of_years_digits':
                # Simplified monthly sum of years digits
                n = asset.category.useful_life_years
                sum_of_digits = Decimal(str(n * (n + 1) / 2))
                depreciable_base = asset.purchase_cost - asset.salvage_value
                
                # Determine which year of life we are in
                diff_years = (target_date.year - asset.purchase_date.year) + (target_date.month - asset.purchase_date.month) / 12.0
                year_index = int(diff_years) # 0-indexed year
                if year_index < n:
                    remaining_life = n - year_index
                    annual_amount = depreciable_base * (Decimal(str(remaining_life)) / sum_of_digits)
                    amount = annual_amount / Decimal('12')

            amount = amount.quantize(Decimal('0.01'))
            
            if amount > 0:
                # Ensure we don't depreciate below salvage value
                if asset.current_value - amount < asset.salvage_value:
                    amount = asset.current_value - asset.salvage_value

                if amount <= 0:
                    continue

                dep_record = Depreciation.objects.create(
                    tenant=tenant,
                    asset=asset,
                    date=target_date,
                    amount=amount
                )
                
                # Update asset carrying value
                asset.current_value -= amount
                asset.save()
                
                # Create Journal Entry
                AssetAccountingService.record_depreciation(dep_record, user)
                
                runs.append(dep_record)
        return runs

class AssetService:
    @staticmethod
    def generate_qr_code(asset):
        """
        Generates a QR code for the asset in SVG format.
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        
        # Data to encode: Asset Number and absolute URL (if possible)
        # For now, just the asset number + internal identifier
        data = f"ASSET:{asset.asset_number}|ID:{asset.pk}"
        
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(data, image_factory=factory, box_size=10)
        
        buffer = BytesIO()
        img.save(buffer)
        return buffer.getvalue().decode('utf-8')

class AssetAccountingService:
    """
    Integrates Asset events with the General Ledger.
    """
    
    @staticmethod
    @transaction.atomic
    def record_acquisition(asset, user):
        """
        Capitalize an asset purchase.
        Dr Asset (Cost)
        Cr Asset Payable / Bank
        """
        tenant = asset.tenant
        category = asset.category
        
        asset_account = category.asset_account
        # We need a payable/clearing account
        try:
            rule = AccountingIntegration.objects.get(tenant=tenant, event_type='asset_acquisition', is_active=True)
            payable_account = rule.credit_account # Or debit? Rule should define.
        except AccountingIntegration.DoesNotExist:
            payable_account = ChartOfAccount.objects.filter(tenant=tenant, account_type='liability_current', name__icontains='Payable').first()

        if not asset_account or not payable_account:
            return None

        # Create Journal Entry... (Simplified call to a helper or directly here)
        # Using the same pattern as HR but for assets.
        pass

    @staticmethod
    @transaction.atomic
    def record_impairment(asset, impairment_loss, reason, user):
        """
        Record IAS 36 Impairment.
        Dr Impairment Loss (Expense)
        Cr Accumulated Impairment/Asset
        """
        tenant = asset.tenant
        category = asset.category
        
        loss_account = category.impairment_account
        asset_account = category.asset_account # Or Accumulated Impairment
        
        if not loss_account or not asset_account:
            raise ValueError("Impairment accounts not configured for category.")

        impairment = AssetImpairment.objects.create(
            tenant=tenant,
            asset=asset,
            date=timezone.now().date(),
            impairment_loss=impairment_loss,
            reason=reason
        )
        
        # update asset carrying amount
        asset.accumulated_impairment += impairment_loss
        asset.current_value -= impairment_loss
        asset.save()
        
        # Post to GL logic here...
        return impairment

    @staticmethod
    @transaction.atomic
    def record_depreciation(dep_record, user):
        """
        Post depreciation to GL.
        Dr Depreciation Expense
        Cr Accumulated Depreciation
        """
        asset = dep_record.asset
        tenant = asset.tenant
        category = asset.category
        
        expense_acc = category.depreciation_account
        accum_acc = category.accumulated_depreciation_account
        
        if not expense_acc or not accum_acc:
            return None

        lines = [
            {'account': expense_acc, 'debit': dep_record.amount, 'credit': 0, 'description': f"Depreciation for {asset.name}"},
            {'account': accum_acc, 'debit': 0, 'credit': dep_record.amount, 'description': f"Accumulated Depreciation for {asset.name}"},
        ]
        
        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=dep_record.date,
            description=f"Depreciation: {asset.name} - {dep_record.date}",
            user=user,
            lines=lines,
            status='posted'
        )
        dep_record.journal_entry = journal
        dep_record.save()
        return journal

    @staticmethod
    @transaction.atomic
    def record_disposal(asset, disposal_date, disposal_type, proceeds, notes, user):
        """
        Record asset disposal per IAS 16.
        1. De-recognize asset cost and accumulated depreciation.
        2. Recognize proceeds (if any).
        3. Record Gain/Loss on disposal.
        """
        tenant = asset.tenant
        category = asset.category
        
        cost = asset.purchase_cost
        accum_dep = cost - asset.current_value # Simplified: Total depreciation + Impairment
        nbv = asset.current_value
        gain_loss = proceeds - nbv
        
        disposal = AssetDisposal.objects.create(
            tenant=tenant,
            asset=asset,
            disposal_date=disposal_date,
            disposal_type=disposal_type,
            disposal_proceeds=proceeds,
            cost_at_disposal=cost,
            accumulated_depreciation_at_disposal=accum_dep,
            net_book_value_at_disposal=nbv,
            gain_loss=gain_loss,
            notes=notes
        )
        
        # Update asset status
        asset.status = 'disposed'
        asset.save()
        
        # Accounting Entry:
        # Dr Bank/Receivable (Proceeds)
        # Dr Accumulated Depreciation (Balance)
        # Dr Loss on Disposal (if NBV > Proceeds)
        # Cr Asset Cost (Original Balance)
        # Cr Gain on Disposal (if Proceeds > NBV)
        
        asset_acc = category.asset_account
        accum_acc = category.accumulated_depreciation_account
        
        # We need a gain/loss account. Ideally from category or integration.
        # Fallback to some default or another category field.
        # For now, let's assume existence of some accounts or use placeholders.
        try:
            integration = AccountingIntegration.objects.get(tenant=tenant, event_type='asset_disposal', is_active=True)
            gain_loss_acc = integration.debit_account # Or similar
        except:
            gain_loss_acc = ChartOfAccount.objects.filter(tenant=tenant, name__icontains='Gain').first() or ChartOfAccount.objects.filter(tenant=tenant, account_type='expense', name__icontains='Loss').first()
            
        lines = [
            {'account': asset_acc, 'debit': 0, 'credit': cost, 'description': f"Derecognize Asset: {asset.name}"},
            {'account': accum_acc, 'debit': accum_dep, 'credit': 0, 'description': f"Derecognize Accum. Dep: {asset.name}"},
        ]
        
        if proceeds > 0:
            # Assume Dr to Bank/Cash for now
            bank_acc = ChartOfAccount.objects.filter(tenant=tenant, is_bank_account=True).first()
            if bank_acc:
                lines.append({'account': bank_acc, 'debit': proceeds, 'credit': 0, 'description': f"Disposal Proceeds: {asset.name}"})
        
        if gain_loss != 0:
            if gain_loss_acc: # Only add if we found a gain/loss account
                if gain_loss > 0:
                    lines.append({'account': gain_loss_acc, 'debit': 0, 'credit': gain_loss, 'description': f"Gain on Disposal: {asset.name}"})
                else:
                    lines.append({'account': gain_loss_acc, 'debit': abs(gain_loss), 'credit': 0, 'description': f"Loss on Disposal: {asset.name}"})
        
        # Validate balance before posting
        total_dr = sum(l['debit'] for l in lines)
        total_cr = sum(l['credit'] for l in lines)
        
        if total_dr != total_cr:
            # Adjust if there's a small discrepancy due to rounding? No, should be exact.
            # For now, raise an error or log it.
            raise ValueError(f"Journal entry for disposal of {asset.name} is out of balance: Dr {total_dr}, Cr {total_cr}")

        journal = JournalService.create_journal_entry(
            tenant=tenant,
            date=disposal_date,
            description=f"Disposal: {asset.name}",
            user=user,
            lines=lines,
            status='posted'
        )
        disposal.journal_entry = journal
        disposal.save()
        return disposal

    @staticmethod
    @transaction.atomic
    def record_revaluation(asset, new_fair_value, user):
        """
        Record IAS 16 Revaluation Surplus.
        Dr Asset (Cost/Fair Value)
        Cr Revaluation Surplus (Equity)
        """
        tenant = asset.tenant
        category = asset.category
        
        adjustment = new_fair_value - asset.current_value
        surplus_account = category.revaluation_surplus_account
        asset_account = category.asset_account
        
        if not surplus_account or not asset_account:
            raise ValueError("Revaluation accounts not configured.")

        rev = AssetRevaluation.objects.create(
            tenant=tenant,
            asset=asset,
            date=timezone.now().date(),
            new_fair_value=new_fair_value,
            adjustment_amount=adjustment
        )
        
        asset.revaluation_surplus += adjustment
        asset.current_value = new_fair_value
        asset.save()
        
        # Post to GL logic here...
        return rev

class AssetReportService:
    @staticmethod
    def get_movement_schedule(tenant, start_date, end_date):
        """
        Generates a roll-forward (movement) schedule for fixed assets.
        Opening Balance + Additions - Disposals +/- Revaluations - Depreciation = Closing Balance
        """
        from django.db.models import Sum, Q
        categories = AssetCategory.objects.filter(tenant=tenant)
        report_data = []

        for cat in categories:
            assets = FixedAsset.objects.filter(tenant=tenant, category=cat)
            
            # Additions
            additions = assets.filter(purchase_date__range=(start_date, end_date)).aggregate(s=Sum('purchase_cost'))['s'] or 0
            
            # Disposals (NBV at time of disposal)
            disposals = AssetDisposal.objects.filter(
                tenant=tenant, 
                asset__category=cat, 
                disposal_date__range=(start_date, end_date)
            ).aggregate(s=Sum('net_book_value_at_disposal'))['s'] or 0
            
            # Depreciation Expense (Periodic)
            dep_charge = Depreciation.objects.filter(
                tenant=tenant,
                asset__category=cat,
                date__range=(start_date, end_date)
            ).aggregate(s=Sum('amount'))['s'] or 0
            
            # Revaluations / Impairments
            revals = AssetRevaluation.objects.filter(
                tenant=tenant,
                asset__category=cat,
                date__range=(start_date, end_date)
            ).aggregate(s=Sum('adjustment_amount'))['s'] or 0
            
            impairments = AssetImpairment.objects.filter(
                tenant=tenant,
                asset__category=cat,
                date__range=(start_date, end_date)
            ).aggregate(s=Sum('impairment_loss'))['s'] or 0

            # Closing Balance
            closing = assets.filter(status__in=['active', 'fully_depreciated']).aggregate(s=Sum('current_value'))['s'] or 0
            
            report_data.append({
                'category': cat.name,
                'opening': closing - additions + disposals - revals + impairments + dep_charge,
                'additions': additions,
                'disposals': disposals,
                'depreciation': dep_charge,
                'revaluations': revals - impairments,
                'closing': closing,
            })
            
        return report_data
