import logging
from .models import PlanModuleAccess, PlanFeatureAccess

logger = logging.getLogger(__name__)

class PlanAccessService:
    """
    Centralized service for managing plan-based module and feature access.
    Synchronizes the JSON features_config on the Plan model with specific 
    PlanModuleAccess and PlanFeatureAccess records for performance.
    """

    @staticmethod
    def sync_plan_access(plan):
        """
        Synchronizes the individual access records from the plan's JSON configuration.
        """
        if not plan.features_config:
            return

        config = plan.features_config
        
        # 1. Sync Modules
        for module_name, module_data in config.items():
            is_enabled = module_data.get('enabled', False)
            display_name = module_data.get('display_name', module_name.title())
            
            PlanModuleAccess.objects.update_or_create(
                plan=plan,
                module_name=module_name,
                defaults={
                    'module_display_name': display_name,
                    'is_available': is_enabled
                }
            )
            
            # 2. Sync Features within Module
            features = module_data.get('features', {})
            for feature_key, feature_enabled in features.items():
                feature_name = feature_key.replace('_', ' ').title()
                
                PlanFeatureAccess.objects.update_or_create(
                    plan=plan,
                    feature_key=feature_key,
                    defaults={
                        'feature_name': feature_name,
                        'is_available': feature_enabled,
                        'feature_category': module_name
                    }
                )
        
        logger.info(f"Synchronized access configuration for plan: {plan.name}")

    @staticmethod
    def get_module_access(plan, module_name):
        """
        Check if a module is accessible for a given plan.
        """
        if not plan:
            return False
            
        try:
            return PlanModuleAccess.objects.get(
                plan=plan, 
                module_name=module_name
            ).is_available
        except PlanModuleAccess.DoesNotExist:
            # Fallback to JSON config if record doesn't exist yet
            return plan.features_config.get(module_name, {}).get('enabled', False)

    @staticmethod
    def get_feature_access(plan, module_name, feature_key):
        """
        Check if a feature is accessible within a module for a given plan.
        """
        if not plan:
            return False

        # First check if the module itself is available
        if not PlanAccessService.get_module_access(plan, module_name):
            return False

        try:
            return PlanFeatureAccess.objects.get(
                plan=plan, 
                feature_key=feature_key
            ).is_available
        except PlanFeatureAccess.DoesNotExist:
            # Fallback to JSON config
            module_config = plan.features_config.get(module_name, {})
            return module_config.get('features', {}).get(feature_key, False)
