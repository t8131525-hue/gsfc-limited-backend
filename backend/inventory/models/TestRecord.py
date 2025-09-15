from django.db import models
from audit_trail.mixins import AuditableMixin
from django.core.exceptions import ValidationError
from ..models import Lab, Product, ProductGrade, Specification
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRecord(AuditableMixin, models.Model):
    specification = models.ForeignKey(
        "inventory.Specification", on_delete=models.PROTECT, related_name="test_records"
    )
    lab = models.ForeignKey(
        "inventory.Lab", on_delete=models.PROTECT, related_name="test_records"
    )

    record_id = models.CharField(
        max_length=20, unique=True, editable=False, null=True, blank=True
    )
    batch_no = models.CharField(max_length=255)
    sample_id = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("RETEST", "Retest"),
        ("RETEST_ORDERED", "Retest Ordered"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    record_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Auto-generated unique test record ID, e.g. TR20250731-01",
    )

    product = models.ForeignKey(
        "inventory.Product", on_delete=models.CASCADE, related_name="test_records"
    )
    product_grade = models.ForeignKey(
        "inventory.ProductGrade",
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
