# inventory/signals.py

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Specification

@receiver(m2m_changed, sender=Specification.parameters.through)
def prevent_locked_spec_parameter_change(sender, instance, action, **kwargs):
    """
    Prevents adding or removing parameters from a Specification that is LOCKED.
    """
    if action in ["pre_add", "pre_remove", "pre_clear"]:
        # REVAMPED: We now check the 'status' instead of 'is_active'.
        if instance.status == 'LOCKED':
            raise ValidationError(
                f"Cannot change parameters on a LOCKED specification (v{instance.version}). "
                f"Create a new version to make changes."
            )