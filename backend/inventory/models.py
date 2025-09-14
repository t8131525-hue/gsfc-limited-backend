# inventory/models.py
import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from audit_trail.mixins import AuditableMixin
from django.utils.timezone import now

from django.contrib.auth import get_user_model  # Import User model

User = get_user_model()  # Get the currently active user model


class Product(AuditableMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    product_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,  # Prevents it from appearing in Django Admin forms
        blank=True,  # Allows the first save to happen before we generate the ID
        help_text="Auto-generated unique identifier for the product, e.g., Product001",
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        permissions = [
            ("can_view_products", "Can view product definitions"),
            ("can_manage_products", "Can add, edit, delete product definitions"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save first to get a primary key (pk)
        if is_new and not self.product_id:
            # Generate ID using the pk, ensuring it's unique
            self.product_id = f"Product{self.pk:003d}"
            # Save again, but only update the product_id field
            super().save(update_fields=["product_id"])


class ProductGrade(AuditableMixin, models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="grades"
    )
    name = models.CharField(max_length=255)  # e.g., E-24, E-30
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "name")  # A grade name must be unique per product
        verbose_name = "Product Grade"
        verbose_name_plural = "Product Grades"
        permissions = [
            ("can_view_product_grades", "Can view product grade definitions"),
            (
                "can_manage_product_grades",
                "Can add, edit, delete product grade definitions",
            ),
        ]

    def clean(self):

        # Rule: A product cannot have grades if it already has direct parameters.
        if (
            self.product
            and ParameterDefinition.objects.filter(
                product=self.product, product_grade__isnull=True
            ).exists()
        ):
            raise ValidationError(
                {
                    "product": f"Product '{self.product.name}' already has direct, grade-less parameters defined. It cannot also have grades."
                }
            )
        super().clean()

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ParameterDefinition(AuditableMixin, models.Model):
    DATA_TYPE_CHOICES = [
        ("INTEGER", "Integer"),
        ("DECIMAL", "Decimal"),
        ("STRING", "String"),
        ("BOOLEAN", "Boolean"),
        ("ENUM", "Enum (Dropdown)"),
    ]

    name = models.CharField(max_length=255)
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
        ProductGrade,
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
        verbose_name = "Parameter Definition"
        verbose_name_plural = "Parameter Definitions"
        permissions = [
            ("can_view_parameter_definitions", "Can view parameter definitions"),
            (
                "can_manage_parameter_definitions",
                "Can add, edit, delete parameter definitions",
            ),
        ]

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
        # Check for uniqueness based on product or product_grade
        # This unique check supplements the unique_together on name if we were to use it.
        # Given our current model and serializer logic for mutual exclusivity, we enforce uniqueness
        # of parameter name within its explicit scope (either product OR product_grade).
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
        self.full_clean()  # Calls clean() before saving
        super().save(*args, **kwargs)

    def __str__(self):
        if self.product:
            return f"{self.name} (Product: {self.product.name})"
        elif self.product_grade:
            return f"{self.name} (Grade: {self.product_grade.product.name} - {self.product_grade.name})"
        return self.name  # Should not happen with clean() method


class TestRecord(AuditableMixin, models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("RETEST", "Retest"),
        ("RETEST_ORDERED", "Retest Ordered"),
    ]
    record_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Auto-generated unique test record ID, e.g. TR20250731-01",
    )

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="test_records"
    )
    product_grade = models.ForeignKey(
        ProductGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_records",
    )
    batch_no = models.CharField(
        max_length=255, help_text="The batch number for the sample, e.g., 'A'"
    )
    sample_id = models.CharField(
        max_length=255,
        help_text="Identifier for the sample tested. Not unique, as retests will share this ID.",
    )
    test_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    analyst = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_tests",
    )
    supervisor_comments = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_tests",
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    retest_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="retests"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Test Record"
        verbose_name_plural = "Test Records"
        permissions = [
            ("can_view_test_records", "Can view test records"),
            ("can_manage_test_records", "Can add, edit, delete test records"),
            ("can_approve_test_records", "Can approve/reject test records"),
            (
                "can_view_all_test_records",
                "Can view all test records from all analysts",
            ),
        ]

    def clean(self):
        # Validate that product_grade is consistent with the product's grade existence
        if self.product:
            has_grades = self.product.grades.exists()
            if has_grades and not self.product_grade:
                raise ValidationError(
                    _(
                        "This product has grades; a specific product grade must be selected for the test record."
                    ),
                    code="product_grade_required",
                )
            if not has_grades and self.product_grade:
                raise ValidationError(
                    _(
                        "This product does not have grades; a product grade cannot be selected for the test record."
                    ),
                    code="product_grade_not_allowed",
                )
            # Ensure selected product_grade belongs to the selected product
            if self.product_grade and self.product_grade.product != self.product:
                raise ValidationError(
                    _(
                        "The selected product grade does not belong to the specified product."
                    ),
                    code="invalid_product_grade_product_mismatch",
                )

        # Ensure that approved_by and approved_at are only set if status is APPROVED or REJECTED
        if self.status not in ["APPROVED", "REJECTED", "RETEST_ORDERED"]:
            if self.approved_by or self.approved_at:
                raise ValidationError(
                    (
                        "Approval details can only be set when the status is 'APPROVED', 'REJECTED', or 'RETEST_ORDERED'."
                    ),
                    code="invalid_approval_details",
                )

    # In inventory/models.py, inside the TestRecord class

    def save(self, *args, **kwargs):
        # Run the model's full_clean validation first
        self.full_clean()

        # Check if this is a new record being created (pk is None)
        is_new = self.pk is None

        # Save the instance to the database
        super().save(*args, **kwargs)

        # Generate the record_id only for new records that don't have one yet
        if is_new and not self.record_id:
            # Use the creation date for consistency
            date_str = self.created_at.strftime("%Y%m%d")

            # Find the highest sequence number for today to avoid race conditions
            last_record_for_today = (
                TestRecord.objects.filter(created_at__date=self.created_at.date())
                .exclude(pk=self.pk)
                .order_by("-record_id")
                .first()
            )

            sequence = 1
            if last_record_for_today and last_record_for_today.record_id:
                try:
                    # Extract the last sequence number and increment it
                    last_sequence = int(last_record_for_today.record_id.split("-")[-1])
                    sequence = last_sequence + 1
                except (ValueError, IndexError):
                    # Fallback just in case of a malformed ID, though unlikely
                    sequence = TestRecord.objects.filter(
                        created_at__date=self.created_at.date()
                    ).count()

            self.record_id = f"TR-{date_str}-{sequence:02d}"

            # Save the instance again, but only update the record_id field
            super().save(update_fields=["record_id"])

    def __str__(self):
        base = f"{self.record_id or 'Unassigned'}: {self.product.name}"
        grade_str = f" - {self.product_grade.name}" if self.product_grade else ""
        retest_str = (
            f" (Retest of {self.retest_of.record_id})" if self.retest_of else ""
        )
        return f"{base}{grade_str} ({self.sample_id}){retest_str}"


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
