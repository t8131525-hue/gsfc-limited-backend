# alerts/management/commands/backfill_alert_ids.py

from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from alerts.models import Alert


class Command(BaseCommand):
    help = "Finds all alerts with a null alert_id and generates a unique ID for them."

    @transaction.atomic
    def handle(self, *args, **options):
        # Find all alerts that need an ID
        alerts_to_update = Alert.objects.filter(alert_id__isnull=True).order_by(
            "created_at"
        )
        count = alerts_to_update.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ No alerts found to update. All alerts already have an ID."
                )
            )
            return

        self.stdout.write(
            f"Found {count} alert(s) needing an ID. Starting backfill process..."
        )

        # Group alerts by their creation date
        alerts_by_date = defaultdict(list)
        for alert in alerts_to_update:
            alerts_by_date[alert.created_at.date()].append(alert)

        updated_count = 0
        # Process each day's alerts
        for date, alerts_on_day in alerts_by_date.items():
            self.stdout.write(
                f"  -> Processing {len(alerts_on_day)} alert(s) for {date.strftime('%Y-%m-%d')}..."
            )

            # Find the highest existing sequence number for this day
            last_alert_on_day = (
                Alert.objects.filter(created_at__date=date, alert_id__isnull=False)
                .order_by("alert_id")
                .last()
            )

            sequence = 0
            if last_alert_on_day and last_alert_on_day.alert_id:
                try:
                    sequence = int(last_alert_on_day.alert_id.split("-")[-1])
                except (ValueError, IndexError):
                    pass  # Keep sequence at 0 if parsing fails

            date_str = date.strftime("%Y%m%d")

            # Assign new IDs to the alerts for this day
            for alert in alerts_on_day:
                sequence += 1
                alert.alert_id = f"AL-{date_str}-{sequence:02d}"
                updated_count += 1

            # Update all alerts for this day in a single database query
            Alert.objects.bulk_update(alerts_on_day, ["alert_id"])

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Successfully updated {updated_count} alert(s).")
        )
