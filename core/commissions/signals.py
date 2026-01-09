from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from opportunities.models import Opportunity
from .utils import calculate_commission
from .models import Commission, CommissionAuditLog
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Opportunity)
def opportunity_commission_signal(sender, instance, created, **kwargs):
    """
    Auto-calculate commission when an Opportunity is marked as Won.
    """
    # Only trigger on update (not create) and when stage is_won
    if not created and instance.stage and instance.stage.is_won:
        # Check if commission already exists for this opportunity and user
        existing = Commission.objects.filter(
            opportunity=instance,
            user=instance.owner
        ).exists()
        
        if not existing:
            commission = calculate_commission(instance)
            if commission:
                commission.tenant = instance.tenant
                commission.save()
                logger.info(f"Created commission {commission.amount} for {instance.owner} on {instance.opportunity_name}")
                
                # Handle Split
                if hasattr(commission, 'split_details') and commission.split_details:
                    from .models import SplitCommission
                    details = commission.split_details
                    SplitCommission.objects.create(
                        main_commission=commission,
                        split_with_user=details['split_with'],
                        split_amount=details['split_amount'],
                        split_percentage=details['split_percentage'],
                        split_type='team_deal', # Default from rule
                        tenant=instance.tenant
                    )
                    logger.info(f"Created split commission {details['split_amount']} for {details['split_with']}")

@receiver(post_save, sender=Commission)
def commission_audit_log_signal(sender, instance, created, **kwargs):
    """
    Create audit log when commission is created or updated
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get the user who made the change (this is a simplified approach)
    # In a real app, you might pass the user from the view
    try:
        # For now, we'll assume it's an admin/system action if no specific user is provided
        # In a real app, this would come from the request context
        performed_by = User.objects.first()  # This is a placeholder - would need proper context
        
        action = 'created' if created else 'updated'
        
        # Create audit log
        CommissionAuditLog.objects.create(
            commission=instance,
            action=action,
            performed_by=performed_by,  # This is a placeholder
            tenant=instance.tenant
        )
    except Exception as e:
        logger.error(f"Error creating audit log: {e}")

@receiver(post_save, sender=Commission)
def commission_status_change_signal(sender, instance, created, **kwargs):
    """
    Log status changes for audit trail
    """
    if not created and hasattr(instance, '_original_status') and instance._original_status != instance.status:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            # Placeholder for actual user who made the change
            performed_by = User.objects.first()
            
            CommissionAuditLog.objects.create(
                commission=instance,
                action=f'status_changed_to_{instance.status}',
                performed_by=performed_by,
                old_values={'status': instance._original_status},
                new_values={'status': instance.status},
                tenant=instance.tenant
            )
        except Exception as e:
            logger.error(f"Error logging status change: {e}")

@receiver(pre_save, sender=Commission)
def commission_pre_save_signal(sender, instance, **kwargs):
    """
    Capture original values before saving for audit trail
    """
    if instance.pk:
        try:
            original = Commission.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Commission.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None