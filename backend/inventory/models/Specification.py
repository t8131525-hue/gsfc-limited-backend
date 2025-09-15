from audit_trail.mixins import AuditableMixin
from django.db import models
from inventory.models import Product, ProductGrade, ParameterDefinition
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class Specification(AuditableMixin, models.Model):
    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for this version, e.g., 'v1.0 - Initial Release'",
    )
    version = models.PositiveIntegerField()
    is_active = models.BooleanField(
        default=True,
        help_text="Is this the current, active specification for new tests?",
    )

    # A Specification is for EITHER a Product OR a ProductGrade
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.CASCADE,
        related_name="specifications",
        null=True,
        blank=True,
    )
    product_grade = models.ForeignKey(
        'inventory.ProductGrade',
        on_delete=models.CASCADE,
        related_name="specifications",
        null=True,
        blank=True,
    )

    # The set of parameters that define this specific version.
    parameters = models.ManyToManyField(
        'inventory.ProductDefinition', related_name="specifications"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of when this version was made active.",
    )

    class Meta:
        # Ensure version numbers are unique per product/grade
        unique_together = [("product", "version"), ("product_grade", "version")]
        verbose_name = "Specification Version"
        verbose_name_plural = "Specification Versions"

    def clean(self):
        # Enforce that either product or product_grade is set, but not both.
        if self.product and self.product_grade:
            raise ValidationError(
                _("A specification can't be for both a Product and a Product Grade.")
            )
        if not self.product and not self.product_grade:
            raise ValidationError(
                _("A specification must be for either a Product or a Product Grade.")
            )

    def save(self, *args, **kwargs):
        if self.is_active and not self.activated_at:
            self.activated_at = now()

        # Enforce only one active version per product/grade
        if self.is_active:
            queryset = Specification.objects.filter(is_active=True)
            if self.product:
                queryset = queryset.filter(product=self.product)
            else:  # self.product_grade
                queryset = queryset.filter(product_grade=self.product_grade)

            queryset.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)

    def __str__(self):
        target = self.product or self.product_grade
        return f"{target} - Spec v{self.version} ({self.name})"
