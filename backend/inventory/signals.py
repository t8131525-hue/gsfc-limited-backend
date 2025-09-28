# inventory/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ParameterDefinition, Version, ProductGrade

# This signal will fire every time a ParameterDefinition is CREATED or UPDATED.
@receiver(post_save, sender=ParameterDefinition)
def parameter_added_to_owner(sender, instance, created, **kwargs):
    """
    Handles logic when a parameter is added or changed on a Version or ProductGrade.
    """
    # Check if the parameter that was saved belongs to a Version
    if isinstance(instance.owner, Version):
        version_instance = instance.owner
        if created:
            print(f"A new parameter '{instance.name}' was ADDED to Version '{version_instance.version_name}'.")
            # ... put your logic here for when a parameter is added ...
        else:
            print(f"Parameter '{instance.name}' was UPDATED on Version '{version_instance.version_name}'.")
            # ... put your logic here for when a parameter is updated ...

    # You can also check if it belongs to a ProductGrade
    elif isinstance(instance.owner, ProductGrade):
        grade_instance = instance.owner
        if created:
            print(f"A new parameter '{instance.name}' was ADDED to Grade '{grade_instance.name}'.")


# This signal will fire every time a ParameterDefinition is DELETED.
@receiver(post_delete, sender=ParameterDefinition)
def parameter_removed_from_owner(sender, instance, **kwargs):
    """

    Handles logic when a parameter is removed from a Version or ProductGrade.
    """
    if isinstance(instance.owner, Version):
        version_instance = instance.owner
        print(f"Parameter '{instance.name}' was REMOVED from Version '{version_instance.version_name}'.")
        # ... put your logic here for when a parameter is removed ...

    elif isinstance(instance.owner, ProductGrade):
        grade_instance = instance.owner
        print(f"Parameter '{instance.name}' was REMOVED from Grade '{grade_instance.name}'.")