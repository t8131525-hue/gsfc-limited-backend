from audit_trail.mixins import AuditableMixin
from django.db import models
from django.core.exceptions import ValidationError
from inventory.models import Product, ParameterDefinition


class ProductGrade(AuditableMixin, models.Model):
    product = models.ForeignKey(
        'inventory.Product', on_delete=models.CASCADE, related_name="grades"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "name")
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
