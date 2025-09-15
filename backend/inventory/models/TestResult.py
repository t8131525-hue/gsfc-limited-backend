from ..models import TestRecord, ParameterDefinition
from django.core.exceptions import ValidationError
from audit_trail.mixins import AuditableMixin
from django.db import models


class TestResult(AuditableMixin, models.Model):
    test_record = models.ForeignKey(
        TestRecord, on_delete=models.CASCADE, related_name="parameter_values"
    )
    parameter = models.ForeignKey(
        ParameterDefinition, on_delete=models.CASCADE, related_name="test_values"
    )
    # Store values based on data_type
    value_decimal = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True
    )
    value_string = models.CharField(max_length=500, blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "test_record",
            "parameter",
        )  # A parameter can only have one value per test record
        verbose_name = "Test Result"
        verbose_name_plural = "Test Results"

    def clean(self):
        """
        Ensures that the correct value field is populated based on the
        parameter's data_type and that the value is valid.
        """
        super().clean()

        param_def = self.parameter
        has_decimal = self.value_decimal is not None
        has_string = self.value_string is not None
        has_boolean = self.value_boolean is not None

        # Count how many value fields are populated
        num_values_provided = sum([has_decimal, has_string, has_boolean])

        if param_def.is_required and num_values_provided == 0:
            raise ValidationError(
                f"A value is required for the required parameter '{param_def.name}'."
            )

        if num_values_provided > 1:
            raise ValidationError(
                "Only one value field (decimal, string, or boolean) should be populated."
            )

        if has_decimal and param_def.data_type not in ["INTEGER", "DECIMAL"]:
            raise ValidationError(
                f"A numeric value is not allowed for the '{param_def.name}' parameter (type: {param_def.data_type})."
            )

        if has_boolean and param_def.data_type != "BOOLEAN":
            raise ValidationError(
                f"A boolean value is not allowed for the '{param_def.name}' parameter (type: {param_def.data_type})."
            )

        if has_string and param_def.data_type not in ["STRING", "ENUM"]:
            raise ValidationError(
                f"A string value is not allowed for the '{param_def.name}' parameter (type: {param_def.data_type})."
            )

        # Specific validation for ENUM types
        if param_def.data_type == "ENUM":
            if self.value_string not in (param_def.enum_options or []):
                raise ValidationError(
                    f"'{self.value_string}' is not a valid option for '{param_def.name}'. "
                    f"Valid options are: {', '.join(param_def.enum_options or [])}"
                )

    def save(self, *args, **kwargs):
        """
        The alert generation logic has been moved to alerts/signals.py.
        This method now only handles validation and saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Value for {self.parameter.name} in Test {self.test_record.id}"
