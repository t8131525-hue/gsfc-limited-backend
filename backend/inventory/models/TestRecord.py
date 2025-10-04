from django.db import models, transaction
from audit_trail.mixins import AuditableMixin
from django.core.exceptions import ValidationError
from ..models import Lab, Product, ProductGrade
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

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
        ("CLOSED", "Closed"),
        ("RETEST_ORDERED", "Retest Ordered"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # User, approval tracking and Time stamps
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
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_tests",
    )
    closed_at = models.DateTimeField(blank=True, null=True)
    retest_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="retests"
    )
    retest_ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordered_retests",
    )
    retest_ordered_at = models.DateTimeField(blank=True, null=True)
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

    def __str__(self):
        base = f"{self.record_id or 'Unassigned'}: {self.version.product.name}"
        grade_str = f" - {self.product_grade.name}" if self.product_grade else ""
        retest_str = (
            f" (Retest of {self.retest_of.record_id})" if self.retest_of else ""
        )
        return f"{base}{grade_str} ({self.sample_id}){retest_str}"

    def _create_retest(self):
        """Creates a new PENDING TestRecord that links back to this one."""
        if not self.retests.exists():  # Ensure we only create one retest
            new_retest = TestRecord.objects.create(
                version=self.version,
                lab=self.lab,
                product_grade=self.product_grade,
                batch_no=self.batch_no,
                sample_id=self.sample_id,
                analyst=None,  # A new analyst will be assigned
                status="PENDING",  # The new record starts as PENDING
                retest_of=self,
            )
            return new_retest
        return None

    def clean(self):
        # --- ENTIRE CLEAN METHOD IS REVAMPED FOR WORKFLOW AND IMMUTABILITY ---
        super().clean()

        # 1. Initial creation checks
        if self.version and self.version.status != "LOCKED":
            raise ValidationError(
                _("Test records can only be created for 'LOCKED' versions.")
            )

        has_grades = self.version.grades.exists()
        if has_grades and not self.product_grade:
            raise ValidationError(
                _(
                    "This product version has grades; a specific product grade must be selected."
                )
            )
        if not has_grades and self.product_grade:
            raise ValidationError(
                _(
                    "This product version does not have grades; a product grade cannot be selected."
                )
            )
        if self.product_grade and self.product_grade.version != self.version:
            raise ValidationError(
                _(
                    "The selected product grade does not belong to the specified product version."
                )
            )

        # 2. Logic for existing records (updates)
        if self.pk:
            original = TestRecord.objects.get(pk=self.pk)
            original_status = original.status

            # Rule: Cannot modify a CLOSED record at all.
            if original_status == "CLOSED":
                raise ValidationError(_("Cannot modify a 'CLOSED' test record."))

            # Rule: Cannot modify most fields of a finalized record.
            # This prevents changing the batch number, sample ID etc. after approval.
            finalized_statuses = ["APPROVED", "REJECTED", "RETEST_ORDERED"]
            if original_status in finalized_statuses:
                # We allow changing status (e.g., from APPROVED to CLOSED)
                # and adding supervisor comments, but nothing else.
                non_editable_fields = [
                    "version",
                    "lab",
                    "product_grade",
                    "batch_no",
                    "sample_id",
                    "analyst",
                ]
                for field in non_editable_fields:
                    if getattr(original, field) != getattr(self, field):
                        raise ValidationError(
                            _(
                                "Cannot change '%(field)s' on a record that is already '%(status)s'."
                            )
                            % {"field": field, "status": original.get_status_display()}
                        )

            # Rule: Enforce state transitions
            # PENDING can only go to APPROVED or REJECTED
            if (
                original_status == "PENDING"
                and self.status != original_status
                and self.status not in ["APPROVED", "REJECTED"]
            ):
                raise ValidationError(
                    _(
                        "A 'Pending' record can only be moved to 'Approved' or 'Rejected'."
                    )
                )

            # RETEST_ORDERED can only be set from APPROVED or REJECTED
            if self.status == "RETEST_ORDERED" and original_status not in [
                "APPROVED",
                "REJECTED",
            ]:
                raise ValidationError(
                    _(
                        "A retest can only be ordered for an 'Approved' or 'Rejected' record."
                    )
                )

            if self.status == "CLOSED" and original_status not in [
                "APPROVED",
                "REJECTED",
                "RETEST_ORDERED",
            ]:
                raise ValidationError(
                    _(
                        "A record can only be 'Closed' from an 'Approved', 'Rejected', or 'Retest Ordered' state."
                    )
                )

    def save(self, *args, **kwargs):
        # Store the status before any changes, but only if the object exists in DB
        original_status = None
        if self.pk:
            original_status = TestRecord.objects.get(pk=self.pk).status

        # Set timestamps for status changes
        if self.status in ["APPROVED", "REJECTED"] and not self.approved_at:
            self.approved_at = timezone.now()
        if self.status == "CLOSED" and not self.closed_at:
            self.closed_at = timezone.now()
        if self.status == "RETEST_ORDERED" and not self.retest_ordered_at:
            self.retest_ordered_at = timezone.now()

        # Run full validation before saving
        self.full_clean()

        # Use a transaction to ensure data integrity
        with transaction.atomic():
            is_new = self.pk is None
            super().save(*args, **kwargs)

            # --- Side Effect: Create retest record AFTER saving the status change ---
            if (
                original_status not in ["RETEST_ORDERED"]
                and self.status == "RETEST_ORDERED"
            ):
                self._create_retest()

            # --- Auto-generate record_id (your existing logic is good) ---
            if is_new and not self.record_id:
                # Use select_for_update to lock rows and prevent race conditions
                last_record = (
                    TestRecord.objects.select_for_update()
                    .filter(created_at__date=self.created_at.date())
                    .exclude(pk=self.pk)
                    .order_by("pk")
                    .last()
                )
                sequence = 1
                if last_record and last_record.record_id:
                    try:
                        last_sequence = int(last_record.record_id.split("-")[-1])
                        sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        pass  # Fallback to 1 if parsing fails

                date_str = self.created_at.strftime("%Y%m%d")
                self.record_id = f"TR-{date_str}-{sequence:02d}"
                # Save only the record_id field to avoid triggering save recursion
                super().save(update_fields=["record_id"])
