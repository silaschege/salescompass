"""
Wazo App Configuration.
"""
from django.apps import AppConfig


class WazoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wazo'
    verbose_name = 'Wazo Telephony'
    
    def ready(self):
        # Import signals if any
        pass
