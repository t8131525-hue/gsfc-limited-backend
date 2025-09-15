# alerts/models.py
from django.db import models
from inventory.models import TestRecord, TestResult


class Alert(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("ACKNOWLEDGED", "Acknowledged"),
        ("RESOLVED", "Resolved"),
    ]

    test_result = models.OneToOneField(
        "inventory.TestResult", on_delete=models.CASCADE, related_name="alert"
    )
    test_record = models.ForeignKey(
        "inventory.TestRecord", on_delete=models.CASCADE, related_name="alerts"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="NEW", db_index=True
    )
    details = models.JSONField(
        help_text="Stores details like the value that triggered the alert and the expected range."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self):
        return f"Alert for Test Record {self.test_record.id} on parameter {self.test_result.parameter.name}"
