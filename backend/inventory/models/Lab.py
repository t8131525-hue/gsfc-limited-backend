from django.db import models
from audit_trail.mixins import AuditableMixin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()


class Lab(AuditableMixin, models.Model):
    """Represents a physical or logical lab where tests are performed."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    # Access Control: Link Labs to Groups and specific Users for permissions
    accessible_by_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="accessible_labs",
        help_text="Groups that have access to perform and view tests in this lab.",
    )
    accessible_by_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="accessible_labs",
        help_text="Specific users who have exceptional access to this lab.",
    )

    def __str__(self):
        return self.name
