from django.db import models, transaction
from audit_trail.mixins import AuditableMixin
from django.core.exceptions import ValidationError
from ..models import Lab, Product, ProductGrade
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRecord(AuditableMixin, models.Model):
    # --- CORRECTED AND FINAL FIELDS ---

    # The Version is the single source of truth for the specification
    version = models.ForeignKey(
        "inventory.Version", on_delete=models.PROTECT, related_name="test_records"
    )
    lab = models.ForeignKey(
        "inventory.Lab", on_delete=models.PROTECT, related_name="test_records"
    )
    product_grade = models.ForeignKey(
        "inventory.ProductGrade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_records",
    )

    # Unique, auto-generated ID
    record_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        help_text="Auto-generated unique test record ID, e.g. TR20250731-01",
    )

    # Batch and sample info
    batch_no = models.CharField(
        max_length=255, help_text="The batch number for the sample, e.g., 'A'"
    )
    sample_id = models.CharField(
        max_length=255,
        help_text="Identifier for the sample tested. Not unique, as retests will share this ID.",
    )

    # Status and workflow
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("RETEST", "Retest"),
        ("RETEST_ORDERED", "Retest Ordered"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # User and approval tracking
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

    # Retest tracking
    retest_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="retests"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- (Your Meta class, clean(), save(), and __str__() methods follow) ---

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

    # In the TestRecord model's clean() method
    def clean(self):
        if self.version:
            # 👇 Corrected logic to check the version, not the product
            has_grades = self.version.grades.exists()

            if has_grades and not self.product_grade:
                raise ValidationError(
                    _(
                        "This product version has grades; a specific product grade must be selected."
                    ),
                    code="product_grade_required",
                )
            if not has_grades and self.product_grade:
                raise ValidationError(
                    _(
                        "This product version does not have grades; a product grade cannot be selected."
                    ),
                    code="product_grade_not_allowed",
                )

            # 👇 Corrected logic to check grade belongs to the version
            if self.product_grade and self.product_grade.version != self.version:
                raise ValidationError(
                    _(
                        "The selected product grade does not belong to the specified product version."
                    ),
                    code="invalid_product_grade_product_mismatch",
                )

            if self.status not in ["APPROVED", "REJECTED", "RETEST_ORDERED"]:
                if self.approved_by or self.approved_at:
                    raise ValidationError(
                        (
                            "Approval details can only be set when the status is 'APPROVED', 'REJECTED', or 'RETEST_ORDERED'."
                        ),
                        code="invalid_approval_details",
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.record_id:
            with transaction.atomic():
                last_record = (
                    TestRecord.objects.select_for_update()
                    .filter(created_at__date=self.created_at.date())
                    .order_by("pk")
                    .last()
                )
                sequence = 1
                if last_record and last_record.record_id:
                    try:
                        last_sequence = int(last_record.record_id.split("-")[-1])
                        sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        pass

                date_str = self.created_at.strftime("%Y%m%d")
                self.record_id = f"TR-{date_str}-{sequence:02d}"
                super().save(update_fields=["record_id"])

    def __str__(self):
        base = f"{self.record_id or 'Unassigned'}: {self.version.product.name}"
        grade_str = f" - {self.product_grade.name}" if self.product_grade else ""
        retest_str = (
            f" (Retest of {self.retest_of.record_id})" if self.retest_of else ""
        )
        return f"{base}{grade_str} ({self.sample_id}){retest_str}"
