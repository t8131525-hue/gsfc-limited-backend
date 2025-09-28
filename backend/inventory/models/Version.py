# inventory/models/Version.py

from audit_trail.mixins import AuditableMixin
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation


# REVAMPED: Renamed class from Specification to Version
class Version(AuditableMixin, models.Model):
    STATUS_CHOICES = [("DRAFT", "Draft"), ("LOCKED", "Locked")]

    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        # REVAMPED: Updated related_name
        related_name="versions",
    )
    parameters = GenericRelation("inventory.ParameterDefinition", related_query_name="version")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")
    version_name = models.CharField(
        max_length=100, help_text="User-defined version, e.g., 'v1.0', '2025 Q4 Update'"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(
        default=False, help_text="Is this the current, active testing yardstick?"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_versions",
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("product", "version_name")]
        # REVAMPED: Updated verbose names
        verbose_name = "Version"
        verbose_name_plural = "Versions"
        permissions = [
            ("can_manage_versions", "Can create, edit, lock, and activate versions")
        ]

    def clean(self):
        # This check should be first
        if self.pk:  # Only check for existing instances
            has_parameters = self.parameters.exists()
            has_grades = self.grades.exists()
            if has_parameters and has_grades:
                raise ValidationError(
                    _(
                        "A Version cannot have both Parameters and Product Grades defined directly. Grades should encapsulate their own parameters."
                    )
                )

        if self.is_active and self.status != "LOCKED":
            raise ValidationError(
                {
                    "is_active": _(
                        "Cannot activate a DRAFT version. Please lock it first."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self.status == "LOCKED" and not self.locked_at:
            self.locked_at = now()

        if self.is_active and not self.activated_at:
            self.activated_at = now()
        elif not self.is_active:
            self.activated_at = None

        if self.is_active:
            # REVAMPED: Use the new class name here
            Version.objects.filter(product=self.product, is_active=True).exclude(
                pk=self.pk
            ).update(is_active=False)

        super().save(*args, **kwargs)

    @transaction.atomic
    def create_new_version_from_this(self):
        # REVAMPED: Use the new class name here
        new_version = Version.objects.create(
            product=self.product,
            created_by=self.created_by,
            version_name=f"Draft of {self.version_name}",
        )
        for grade in self.grades.all():
            grade.pk = None
            # REVAMPED: Link to the new 'version' instance
            grade.version = new_version
            grade.save()
        
        for param in self.parameters.all():
            param.pk = None
            # REVAMPED: Link to the new 'version' instance
            param.owner = new_version 
            param.save()
            
        return new_version

    def __str__(self):
        return f"{self.product.name} - Version ({self.version_name})"
