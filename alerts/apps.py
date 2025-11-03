# alerts/apps.py
from django.apps import AppConfig

class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'

    def ready(self):
        # This line is essential to connect the signal handlers
        import alerts.signals