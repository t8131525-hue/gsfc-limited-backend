# inventory/signals.py

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Specification

@receiver(m2m_changed, sender=Specification.parameters.through)
def prevent_active_spec_parameter_change(sender, instance, action, **kwargs):
    """
    Prevents adding or removing parameters from a Specification that is active.
    This enforces the 'immutable contract' rule for historical data integrity.
    """
    if action in ["pre_add", "pre_remove", "pre_clear"]:
        # 'instance' here is the Specification object being modified.
        if instance.is_active:
            raise ValidationError(
                f"Cannot change parameters on an active specification (v{instance.version}). "
                f"Please create a new version to make changes."
            )