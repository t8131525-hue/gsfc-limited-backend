from django.db import models
from audit_trail.mixins import AuditableMixin


class Product(AuditableMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    product_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,  
        blank=True,
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
        super().save(*args, **kwargs)  
        if is_new and not self.product_id:
            self.product_id = f"Product{self.pk:003d}"
            super().save(update_fields=["product_id"])
