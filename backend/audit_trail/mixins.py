# audit_trail/mixins.py
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from .request import get_current_request


class AuditableMixin:
    """
    A self-contained and robust mixin for audit logging that reliably
    tracks changes without interfering with Django's model initialization.
    """

    # ✅ REMOVED: The __init__ and _initial_state logic that was causing
    # the recursion error during model instantiation.

    def _get_snapshot(self):
        """
        Helper to capture the object's current state. For relational fields,
        it captures the ID to prevent recursive database queries.
        """
        snapshot = {}
        for field in self._meta.fields:
            if field.is_relation:
                snapshot[field.name] = getattr(self, field.attname)
            else:
                snapshot[field.name] = getattr(self, field.name)
        return snapshot

    def save(self, *args, **kwargs):
        is_creating = not self.pk
        change_details = {}

        # ✅ CHANGED: For updates, we now fetch the original state directly
        # from the database right before saving. This is much safer.
        if not is_creating:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                old_state = old_instance._get_snapshot()
                new_state = (
                    self._get_snapshot()
                )  # Snapshot of the current, modified instance

                for field_name, old_value in old_state.items():
                    # Exclude fields that are not useful to track in this manner
                    if field_name in [
                        "id",
                        "created_at",
                        "updated_at",
                        "password",
                        "locked_at",
                        "activated_at",
                    ]:
                        continue

                    new_value = new_state.get(field_name)
                    if str(old_value) != str(new_value):
                        change_details[field_name] = {
                            "old": str(old_value),
                            "new": str(new_value),
                        }
            except self.__class__.DoesNotExist:
                # This can happen in rare edge cases, so we treat it as a new creation.
                is_creating = True

        # Perform the actual save operation first.
        super().save(*args, **kwargs)

        # Now, proceed with logging based on the changes we detected.
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None

        if is_creating:
            AuditLog.objects.create(
                user=user,
                action_type="CREATE",
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                object_repr=str(self),
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
            )
        elif change_details:
            AuditLog.objects.create(
                user=user,
                action_type="UPDATE",
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.pk,
                object_repr=str(self),
                change_details=change_details,
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
            )

    def delete(self, *args, **kwargs):
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None

        # Log the deletion before the object is gone from the database.
        AuditLog.objects.create(
            user=user,
            action_type="DELETE",
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            object_repr=str(self),
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
        )
        # The error was happening when the view tried to *fetch* the object
        # before calling delete(). The actual delete logic here is fine.
        super().delete(*args, **kwargs)
