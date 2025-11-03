# audit_trail/utils.py
from .models import AuditLog
from .request import get_current_request # <-- Corrected import
from django.contrib.contenttypes.models import ContentType

def log_custom_event(instance, action_type, details, user=None):
    """A centralized function for logging non-CRUD business events."""
    request = get_current_request()
    if user is None and request and request.user.is_authenticated:
        user = request.user
    
    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        content_type=ContentType.objects.get_for_model(instance),
        object_id=str(instance.pk),
        object_repr=str(instance),
        change_details=details,
        ip_address=request.META.get('REMOTE_ADDR') if request else None
    )