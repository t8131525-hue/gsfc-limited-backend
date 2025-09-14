# audit_trail/models.py
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

class AuditLog(models.Model):
    # Who performed the action
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text="User who performed the action")

    # When the action was performed
    action_time = models.DateTimeField(auto_now_add=True)

    # Type of action (e.g., CREATE, UPDATE, DELETE, APPROVE, REJECT, LOGIN)
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        # Add more if needed, e.g., 'PASSWORD_CHANGE'
    ]
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, db_index=True)

    # What object was affected (using GenericForeignKey for flexibility)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True, db_index=True) # CharField for flexibility (UUIDs, etc.)
    content_object = GenericForeignKey('content_type', 'object_id')

    # String representation of the affected object
    object_repr = models.CharField(max_length=255, blank=True, null=True)

    # Details of changes, especially for 'UPDATE' actions
    # Stores a JSON object like {"field_name": ["old_value", "new_value"]}
    change_details = models.JSONField(blank=True, null=True,
                                      help_text="JSON details of changes (e.g., {'field': ['old', 'new']})")

    # Optional: IP address of the request
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-action_time']
        permissions = [
            ("can_view_audit_logs", "Can view audit logs"),
        ]

    def __str__(self):
        user_info = self.user.username if self.user else "Anonymous"
        object_info = self.object_repr if self.object_repr else "N/A"
        return f"[{self.action_time.strftime('%Y-%m-%d %H:%M:%S')}] {user_info} {self.action_type} {object_info}"