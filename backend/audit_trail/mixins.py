# audit_trail/mixins.py
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from .request import get_current_request

class AuditableMixin:
    """
    A self-contained and robust mixin for audit logging that reliably
    tracks changes without re-querying the database during save.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On initialization, store the primary key and a snapshot of the data.
        self._initial_pk = self.pk
        self._initial_state = self._get_snapshot()

    def _get_snapshot(self):
        """Helper to capture the object's current state as a dictionary."""
        return {f.name: getattr(self, f.name) for f in self._meta.fields}

    def save(self, *args, **kwargs):
        # An object is new if its initial primary key was None.
        is_creating = self._initial_pk is None
        change_details = {}

        # For updates, calculate changes BEFORE the new state is saved.
        if not is_creating:
            new_state = self._get_snapshot()
            for field_name, old_value in self._initial_state.items():
                if field_name in ['id', 'created_at', 'updated_at', 'password']:
                    continue
                
                new_value = new_state.get(field_name)
                if str(old_value) != str(new_value):
                    change_details[field_name] = {'old': str(old_value), 'new': str(new_value)}

        # Perform the actual save operation.
        super().save(*args, **kwargs)

        # Now that the object is saved, update its internal state for any future saves.
        self._initial_pk = self.pk
        self._initial_state = self._get_snapshot()
        
        # Proceed with logging.
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None
        
        if is_creating:
            AuditLog.objects.create(
                user=user,
                action_type='CREATE',
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                object_repr=str(self),
                ip_address=request.META.get('REMOTE_ADDR') if request else None
            )
        elif change_details:  # Only log an update if something actually changed.
            AuditLog.objects.create(
                user=user,
                action_type='UPDATE',
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                object_repr=str(self),
                change_details=change_details,
                ip_address=request.META.get('REMOTE_ADDR') if request else None
            )

    def delete(self, *args, **kwargs):
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None

        AuditLog.objects.create(
            user=user,
            action_type='DELETE',
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            object_repr=str(self),
            ip_address=request.META.get('REMOTE_ADDR') if request else None
        )
        super().delete(*args, **kwargs)