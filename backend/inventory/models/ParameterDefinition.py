from audit_trail.mixins import AuditableMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ParameterDefinition(AuditableMixin, models.Model):
    # This defines the "owner" of the parameter (either a Version or a ProductGrade)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    owner = GenericForeignKey("content_type", "object_id")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    DATA_TYPE_CHOICES = [
        ("INTEGER", "Integer"),
        ("DECIMAL", "Decimal"),
        ("STRING", "String"),
        ("BOOLEAN", "Boolean"),
        ("ENUM", "Enum (Dropdown)"),
    ]
    data_type = models.CharField(max_length=10, choices=DATA_TYPE_CHOICES)
    unit = models.CharField(max_length=50, blank=True, null=True)
    is_required = models.BooleanField(default=True)
    enum_options = models.JSONField(
        blank=True,
        null=True,
        help_text='For ENUM type, provide options as a JSON array, e.g., ["Option1", "Option2"]',
    )
    # Min/Max values now live here to define the parameter's range
    min_value = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    max_value = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    boolean_true_label = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Custom label for the 'true' value, e.g., 'Present', 'Yes'.",
    )
    boolean_false_label = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Custom label for the 'false' value, e.g., 'Absent', 'No'.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A parameter is unique to its owner, name, and unit
        unique_together = ("content_type", "object_id", "name", "unit")
        verbose_name = "Parameter Definition"
        verbose_name_plural = "Parameter Definitions"

    def __str__(self):
        return f"{self.name}" + (f" ({self.unit})" if self.unit else "")

    def clean(self):
        # Validation to check if the owner belongs to a LOCKED version
        is_locked = False
        owner_obj = self.owner
        if hasattr(owner_obj, "status") and owner_obj.status == "LOCKED":
            is_locked = True
        elif hasattr(owner_obj, "version") and owner_obj.version.status == "LOCKED":
            is_locked = True

        if is_locked:
            raise ValidationError(
                _(
                    "Cannot add or change parameters on an item that belongs to a LOCKED version."
                )
            )

        # (The rest of your original, excellent validation logic for ENUM/BOOLEAN remains)
        if self.data_type == "ENUM":
            if not self.enum_options:
                raise ValidationError(
                    _("ENUM type parameters require 'enum_options'."),
                    code="enum_options_required",
                )
            if not isinstance(self.enum_options, list):
                raise ValidationError(
                    _("'enum_options' must be a JSON array."),
                    code="enum_options_invalid_format",
                )
        else:
            if self.enum_options:
                raise ValidationError(
                    _("'enum_options' can only be set for ENUM data type."),
                    code="enum_options_not_allowed",
                )

        if self.data_type == "BOOLEAN":
            if not self.boolean_true_label or not self.boolean_false_label:
                raise ValidationError(
                    _(
                        "For BOOLEAN data type, both 'True Label' and 'False Label' are required."
                    ),
                    code="boolean_labels_required",
                )
        else:
            if self.boolean_true_label or self.boolean_false_label:
                raise ValidationError(
                    _("Boolean labels can only be set for the BOOLEAN data type."),
                    code="boolean_labels_not_allowed",
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
