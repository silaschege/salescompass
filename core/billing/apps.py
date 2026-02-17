from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'

    def ready(self):
        # Import signal handlers to register them
        import billing.signals
