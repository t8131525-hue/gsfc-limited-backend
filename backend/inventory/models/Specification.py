# inventory/models/Specification.py

from audit_trail.mixins import AuditableMixin
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class Specification(AuditableMixin, models.Model):
    # NEW: Status field to manage the Draft -> Locked workflow
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("LOCKED", "Locked"),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="DRAFT",
        help_text="DRAFT specs can be edited. LOCKED specs are immutable historical records.",
    )

    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for this version, e.g., 'v1.0 - Initial Release'",
    )
    version = models.PositiveIntegerField()
    is_active = models.BooleanField(
        default=False,
        help_text="Is this the current, active specification for new tests? Only LOCKED specs can be active.",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="specifications",
        null=True,
        blank=True,
    )
    product_grade = models.ForeignKey(
        "inventory.ProductGrade",
        on_delete=models.CASCADE,
        related_name="specifications",
        null=True,
        blank=True,
    )
    parameters = models.ManyToManyField(
        "inventory.ParameterDefinition", related_name="specifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of when this version was made active.",
    )

    class Meta:
        unique_together = [("product", "version"), ("product_grade", "version")]
        verbose_name = "Specification Version"
        verbose_name_plural = "Specification Versions"

    def clean(self):
        if self.product and self.product_grade:
            raise ValidationError(
                _("A specification can't be for both a Product and a Product Grade.")
            )
        if not self.product and not self.product_grade:
            raise ValidationError(
                _("A specification must be for either a Product or a Product Grade.")
            )

        # NEW: Add a rule to ensure only LOCKED specs can be made active.
        if self.is_active and self.status != "LOCKED":
            raise ValidationError(
                {
                    "is_active": _(
                        "Cannot activate a specification that is still a DRAFT. Please lock it first."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self.pk is None and not self.version:
            latest_spec = (
                Specification.objects.filter(
                    product=self.product, product_grade=self.product_grade
                )
                .order_by("-version")
                .first()
            )
            self.version = latest_spec.version + 1 if latest_spec else 1

        if self.is_active and not self.activated_at:
            self.activated_at = now()
        elif not self.is_active:
            self.activated_at = None

        if self.is_active:
            queryset = Specification.objects.filter(is_active=True)
            if self.product:
                queryset = queryset.filter(product=self.product)
            else:
                queryset = queryset.filter(product_grade=self.product_grade)
            queryset.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    @transaction.atomic
    def create_new_version(self):
        if not self.pk:
            raise Exception("Cannot create a new version of an unsaved specification.")

        current_parameters = list(self.parameters.all())

        new_spec = Specification(
            name=f"{self.name} (v{self.version + 1})",
            version=self.version + 1,
            # REVAMPED: New versions are always inactive drafts.
            status="DRAFT",
            is_active=False,
            product=self.product,
            product_grade=self.product_grade,
        )
        new_spec.save()
        new_spec.parameters.set(current_parameters)

        return new_spec

    def __str__(self):
        target = self.product or self.product_grade
        return f"{target} - Spec v{self.version} ({self.name})"
