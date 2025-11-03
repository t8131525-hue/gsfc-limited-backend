# audit_trail/apps.py
from django.apps import AppConfig

class AuditTrailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_trail'
    verbose_name = 'Audit Trail'

    # The ready() method MUST be empty.
    def ready(self):
        pass