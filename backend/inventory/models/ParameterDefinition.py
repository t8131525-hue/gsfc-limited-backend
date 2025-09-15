from audit_trail.mixins import AuditableMixin
from django.db import models
from inventory.models import Product
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ParameterDefinition(AuditableMixin, models.Model):
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
    min_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="The minimum normal value for this parameter.",
    )
    max_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="The maximum normal value for this parameter.",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="parameters",
        null=True,
        blank=True,
    )
    product_grade = models.ForeignKey(
        'inventory.ProductGrade',
        on_delete=models.CASCADE,
        related_name="parameters",
        null=True,
        blank=True,
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
        # A parameter is now unique by its name and unit, making it a reusable component.
        unique_together = ("name", "unit")
        verbose_name = "Parameter Definition (Library)"
        verbose_name_plural = "Parameter Definitions (Library)"

    def __str__(self):
        return f"{self.name}" + (f" ({self.unit})" if self.unit else "")

    def clean(self):
        # Enforce that either product or product_grade is set, but not both.
        if self.product and self.product_grade:
            raise ValidationError(
                _(
                    "A parameter definition cannot be associated with both a Product and a Product Grade. Select EITHER one or the other."
                ),
                code="invalid_scope",
            )
        if not self.product and not self.product_grade:
            raise ValidationError(
                _(
                    "A parameter definition must be associated with either a Product or a Product Grade."
                ),
                code="missing_scope",
            )

        # Validate enum_options for ENUM type
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
            if not all(isinstance(item, str) for item in self.enum_options):
                raise ValidationError(
                    _("All items in 'enum_options' must be strings."),
                    code="enum_options_invalid_items",
                )
        else:
            if self.enum_options:
                raise ValidationError(
                    _("'enum_options' can only be set for ENUM data type."),
                    code="enum_options_not_allowed",
                )
            # Validate that boolean labels are handled correctly.
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
        queryset = ParameterDefinition.objects.all()
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        if self.product:
            if queryset.filter(
                name=self.name, product=self.product, product_grade__isnull=True
            ).exists():
                raise ValidationError(
                    _("A parameter with this name already exists for this product."),
                    code="duplicate_product_parameter",
                )
        elif self.product_grade:
            if queryset.filter(
                name=self.name, product_grade=self.product_grade
            ).exists():
                raise ValidationError(
                    _(
                        "A parameter with this name already exists for this product grade."
                    ),
                    code="duplicate_grade_parameter",
                )

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)
