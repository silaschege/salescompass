from django.apps import AppConfig


class QualityControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quality_control'

    def ready(self):
        import quality_control.signals
