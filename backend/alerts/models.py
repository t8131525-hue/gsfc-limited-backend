# alerts/models.py
from django.db import models, transaction
from inventory.models import TestRecord, TestResult


class Alert(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("ACKNOWLEDGED", "Acknowledged"),
        ("RESOLVED", "Resolved"),
    ]

    alert_id = models.CharField(
        max_length=20, unique=True, editable=False, null=True, blank=True
    )

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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.alert_id:
            with transaction.atomic():
                last_alert = (
                    Alert.objects.select_for_update()
                    .filter(created_at__date=self.created_at.date())
                    .exclude(pk=self.pk)
                    .order_by("pk")
                    .last()
                )
                sequence = 1
                if last_alert and last_alert.alert_id:
                    try:
                        last_sequence = int(last_alert.alert_id.split("-")[-1])
                        sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        pass

                date_str = self.created_at.strftime("%Y%m%d")
                self.alert_id = f"AL-{date_str}-{sequence:02d}"
                super().save(update_fields=["alert_id"])

    def __str__(self):
        return f"Alert {self.alert_id} for Test Record {self.test_record.record_id}"
