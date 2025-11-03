# inventory/management/commands/update_legacy_ids.py

from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import TestRecord
from alerts.models import Alert

class Command(BaseCommand):
    help = "Converts old, hyphenated record and alert IDs to the new format."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting legacy ID conversion..."))

        try:
            with transaction.atomic():
                self.update_test_records()
                self.update_alerts()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            self.stdout.write(self.style.WARNING("Transaction rolled back. No data was changed."))
            return

        self.stdout.write(self.style.SUCCESS("All legacy IDs have been successfully updated! ✨"))

    def update_test_records(self):
        """Finds and converts old TestRecord IDs."""
        self.stdout.write("--> Searching for old TestRecord IDs...")
        records_to_update = TestRecord.objects.filter(record_id__contains='-')
        count = records_to_update.count()

        if count == 0:
            self.stdout.write(self.style.NOTICE("    No old TestRecord IDs found to update."))
            return

        self.stdout.write(f"    Found {count} records to update.")

        for record in records_to_update:
            try:
                parts = record.record_id.split('-')
                date_part, sequence_part = parts[1], parts[2]
                year, month, day = date_part[0:4], date_part[4:6], date_part[6:8]
                
                # Calculate the new ID
                new_id = f"TR{day}{month}{year}{int(sequence_part):06d}"

                # MODIFIED: Use QuerySet.update() to bypass model's save() and clean() methods
                TestRecord.objects.filter(pk=record.pk).update(record_id=new_id)

            except (ValueError, IndexError):
                self.stdout.write(self.style.WARNING(f"    Could not parse TestRecord ID: {record.id} - Skipping."))
                continue
        
        self.stdout.write(self.style.SUCCESS(f"--> Finished updating {count} TestRecords."))

    def update_alerts(self):
        """Finds and converts old Alert IDs."""
        self.stdout.write("--> Searching for old Alert IDs...")
        alerts_to_update = Alert.objects.filter(alert_id__contains='-')
        count = alerts_to_update.count()

        if count == 0:
            self.stdout.write(self.style.NOTICE("    No old Alert IDs found to update."))
            return

        self.stdout.write(f"    Found {count} alerts to update.")

        for alert in alerts_to_update:
            try:
                parts = alert.alert_id.split('-')
                date_part, sequence_part = parts[1], parts[2]
                year, month, day = date_part[0:4], date_part[4:6], date_part[6:8]

                # Calculate the new ID
                new_id = f"AL{day}{month}{year}{int(sequence_part):06d}"
                
                # MODIFIED: Using .update() here too for consistency and efficiency
                Alert.objects.filter(pk=alert.pk).update(alert_id=new_id)

            except (ValueError, IndexError):
                self.stdout.write(self.style.WARNING(f"    Could not parse Alert ID: {alert.id} - Skipping."))
                continue

        self.stdout.write(self.style.SUCCESS(f"--> Finished updating {count} Alerts."))