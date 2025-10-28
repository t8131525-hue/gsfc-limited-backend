from django.db import models
from audit_trail.mixins import AuditableMixin
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    
@receiver(post_save, sender=Product)
def assign_product_id(sender, instance, created, **kwargs):
    if created and not instance.product_id:
        instance.product_id = f"Product{instance.pk:003d}"
        Product.objects.filter(pk=instance.pk).update(product_id=instance.product_id)