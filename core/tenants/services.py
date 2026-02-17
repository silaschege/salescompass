from .models import TenantFeatureEntitlement
 
 
 

class FeatureToggleService:
    @staticmethod
    def enable_feature_for_tenant(tenant, feature_key, feature_name, entitlement_type='custom', notes=''):
        """Enable a feature for a specific tenant"""
        entitlement, created = TenantFeatureEntitlement.objects.update_or_create(
            tenant=tenant,
            feature_key=feature_key,
            defaults={
                'feature_name': feature_name,
                'is_enabled': True,
                'entitlement_type': entitlement_type,
                'notes': notes
            }
        )
        return entitlement, created
    
    @staticmethod
    def disable_feature_for_tenant(tenant, feature_key):
        """Disable a feature for a specific tenant"""
        try:
            entitlement = TenantFeatureEntitlement.objects.get(
                tenant=tenant,
                feature_key=feature_key
            )
            entitlement.is_enabled = False
            entitlement.save()
            return entitlement
        except TenantFeatureEntitlement.DoesNotExist:
            return None
    
    @staticmethod
    def setup_trial_feature(tenant, feature_key, feature_name, days=14):
        """Set up a trial feature for a tenant"""
        from django.utils import timezone
        from datetime import timedelta
        
        trial_end = timezone.now() + timedelta(days=days)
        
        entitlement, created = TenantFeatureEntitlement.objects.update_or_create(
            tenant=tenant,
            feature_key=feature_key,
            defaults={
                'feature_name': feature_name,
                'is_enabled': True,
                'entitlement_type': 'trial',
                'trial_start_date': timezone.now(),
                'trial_end_date': trial_end,
                'notes': f'Trial period: {days} days'
            }
        )
        return entitlement, created
    
    @staticmethod
    def bulk_feature_entitlement(tenant, features_data):
        """Bulk update feature entitlements for a tenant"""
        results = []
        for feature_data in features_data:
            feature_key = feature_data['feature_key']
            feature_name = feature_data.get('feature_name', feature_key.replace('_', ' ').title())
            is_enabled = feature_data.get('is_enabled', True)
            entitlement_type = feature_data.get('entitlement_type', 'plan_based')
            notes = feature_data.get('notes', '')
            
            entitlement, created = TenantFeatureEntitlement.objects.update_or_create(
                tenant=tenant,
                feature_key=feature_key,
                defaults={
                    'feature_name': feature_name,
                    'is_enabled': is_enabled,
                    'entitlement_type': entitlement_type,
                    'notes': notes
                }
            )
            results.append({
                'entitlement': entitlement,
                'created': created
            })
        return results
    
    @staticmethod
    def get_accessible_features_for_tenant(tenant):
        """Get all features accessible to a tenant based on plan and explicit entitlements"""
        from .models import TenantFeatureEntitlement
        from billing.models import PlanFeatureAccess
        
        # Get explicitly set features
        explicit_features = TenantFeatureEntitlement.objects.filter(
            tenant=tenant,
            is_enabled=True
        )
        
        # Get features from plan
        plan_features = []
        if tenant.plan:
            plan_features = PlanFeatureAccess.objects.filter(
                plan=tenant.plan,
                is_available=True
            )
        
        # Combine both sources
        accessible_features = []
        for entitlement in explicit_features:
            accessible_features.append({
                'key': entitlement.feature_key,
                'name': entitlement.feature_name,
                'type': entitlement.entitlement_type,
                'source': 'explicit'
            })
        
        for plan_feature in plan_features:
            # Only add if not already explicitly set
            if not any(f['key'] == plan_feature.feature_key for f in accessible_features):
                accessible_features.append({
                    'key': plan_feature.feature_key,
                    'name': plan_feature.feature_name,
                    'type': 'plan_based',
                    'source': 'plan'
                })
        
        return accessible_features