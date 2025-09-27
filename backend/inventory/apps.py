# inventory/apps.py

from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    # NEW: This method ensures your signals are registered when the app starts.
    def ready(self):
        import inventory.signals