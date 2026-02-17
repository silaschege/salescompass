from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Proposal
from opportunities.models import Opportunity, OpportunityStage

@receiver(post_save, sender=Proposal)
def update_opportunity_stage_on_proposal_change(sender, instance, created, **kwargs):
    """
    Automatically update the opportunity stage based on proposal status changes.
    This implements the "Auto-proposal stage updates" feature from the checklist.
    """
    # Skip if this is a new proposal or if we're in a recursive save
    if created or not instance.opportunity:
        return

    # Mapping of proposal statuses to opportunity stage names
    # This mapping follows common sales process flows
    status_to_stage_mapping = {
        'sent': 'proposal',           # When proposal is sent, opportunity enters proposal stage
        'viewed': 'proposal',         # When proposal is viewed, opportunity remains in proposal stage
        'accepted': 'negotiation',    # When proposal is accepted, opportunity moves to negotiation
        'rejected': 'proposal',       # When proposal is rejected, opportunity stays in proposal stage
    }
    
    # Get the target stage name based on proposal status
    target_stage_name = status_to_stage_mapping.get(instance.status)
    
    # If there's no mapping for this status, do nothing
    if not target_stage_name:
        return
    
    try:
        # Use atomic transaction to ensure data consistency
        with transaction.atomic():
            # Get the current opportunity
            opportunity = instance.opportunity
            
            # Check if there's already a stage with the target name for this tenant
            try:
                target_stage = OpportunityStage.objects.get(
                    opportunity_stage_name__iexact=target_stage_name,
                    tenant_id=opportunity.tenant_id
                )
            except OpportunityStage.DoesNotExist:
                # If no stage exists with this name, we can't update, so return silently
                return
            
            # Only update if the current opportunity stage is different from the target stage
            if opportunity.stage != target_stage:
                opportunity.stage = target_stage
                
                # Update probability to match the stage's default probability
                if hasattr(target_stage, 'probability'):
                    # Convert from percentage (0-100) to decimal (0-1) if needed
                    if target_stage.probability > 1:
                        opportunity.probability = float(target_stage.probability) / 100
                    else:
                        opportunity.probability = float(target_stage.probability)
                
                # Save the opportunity with updated stage and probability
                opportunity.save(update_fields=['stage', 'probability'])
                
    except Exception:
        # Silently fail to avoid disrupting the main flow
        # In production, you might want to log this exception
        pass