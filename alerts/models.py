# alerts/models.py
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


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
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="acknowledged_alerts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="resolved_alerts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def save(self, *args, **kwargs):
        if self.pk is None and not self.created_at:
            self.created_at = timezone.now()

        if self.pk is None:
            self.full_clean()

        super().save(*args, **kwargs)

    def clean(self):
        """
        Custom validation, primarily to handle the alert_id generation logic
        and prevent creating new alerts if the daily limit is reached.
        """
        super().clean()
        if self.pk is None and not self.alert_id:  # Only on creation
            with transaction.atomic():
                last_alert = (
                    Alert.objects.select_for_update()
                    .filter(created_at__date=self.created_at.date())
                    .order_by("pk")
                    .last()
                )
                sequence = 1
                if last_alert and last_alert.alert_id:
                    try:
                        # Parse sequence from 'ALDDMMYYYYNNNNNN'
                        last_sequence = int(last_alert.alert_id[10:])
                        sequence = last_sequence + 1
                    except (ValueError, IndexError):
                        pass  # Fallback to 1

                # NEW: Add edge case to enforce the daily limit
                if sequence > 9999999:
                    raise ValidationError(
                        "Maximum daily alert limit (9,999,999) has been reached. "
                        "Cannot create new alert."
                    )

                # Change date format to DDMMYYYY
                date_str = self.created_at.strftime("%d%m%Y")

                # New format with 7-digit padding
                self.alert_id = f"AL{date_str}{sequence:07d}"

    def __str__(self):
        alert_id_display = self.alert_id or "Unassigned"
        return f"Alert {alert_id_display} for Test Record {self.test_record.record_id}"
