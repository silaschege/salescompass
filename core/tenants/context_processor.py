def white_label_context(request):
    """
    Context processor to add white-label branding settings to all templates
    """
    if hasattr(request.user, 'tenant') and request.user.tenant:
        try:
            white_label_settings = request.user.tenant.white_label_settings
            return {
                'white_label_settings': white_label_settings,
            }
        except:
            # If no white-label settings exist, return empty context
            return {
                'white_label_settings': None,
            }
    else:
        return {
            'white_label_settings': None,
        }

def feature_flags(request):
    """Add feature flags to all template contexts"""
    from .utils import get_accessible_features
    if request.user.is_authenticated and hasattr(request.user, 'tenant'):
        features = get_accessible_features(request.user.tenant)
        feature_keys = [f['key'] for f in features]
        return {
            'feature_flags': feature_keys,
            'accessible_features': features
        }
    return {
        'feature_flags': [],
        'accessible_features': []
    }