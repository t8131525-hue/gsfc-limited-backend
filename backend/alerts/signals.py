# alerts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from inventory.models import TestResult
from .models import Alert

@receiver(post_save, sender=TestResult)
def create_alert_on_out_of_range(sender, instance, **kwargs):
    """
    Listens for when a TestResult is saved and creates an Alert if the
    value is outside the defined normal range.
    """
    param_def = instance.parameter
    value_to_check = instance.value_decimal

    # Proceed only if the parameter has defined limits and a value was entered
    if value_to_check is not None and param_def.min_value is not None and param_def.max_value is not None:
        is_out_of_range = not (param_def.min_value <= value_to_check <= param_def.max_value)
        
        if is_out_of_range:
            # Create the alert if the value is bad. get_or_create prevents duplicates.
            Alert.objects.get_or_create(
                test_result=instance,
                defaults={
                    'test_record': instance.test_record,
                    'details': {
                        'value_entered': float(value_to_check),
                        'normal_range': f"{float(param_def.min_value)} - {float(param_def.max_value)}",
                        'parameter_name': param_def.name,
                        'sample_id': instance.test_record.sample_id,
                    }
                }
            )