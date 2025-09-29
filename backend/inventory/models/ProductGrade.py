from audit_trail.mixins import AuditableMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation



class ProductGrade(AuditableMixin, models.Model):
    version = models.ForeignKey(
    "inventory.Version", on_delete=models.CASCADE, related_name="grades"
    )
    parameters = GenericRelation("inventory.ParameterDefinition")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("version", "name")
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
        # NEW: Validation to ensure grades can only be added to a DRAFT specification.
        if self.version and self.version.status == "LOCKED":
            raise ValidationError(
                _(
                    "Cannot add or change grades on a LOCKED version. Create a new version."
                )
            )
        super().clean()

    def __str__(self):
        return f"{self.version.product.name} - {self.name} (Version: {self.version.version_name})"
