# inventory/management/commands/backfill_record_ids.py

from django.core.management.base import BaseCommand
from inventory.models import TestRecord

class Command(BaseCommand):
    help = 'Backfills the unique record_id for existing TestRecord objects that do not have one.'

    def handle(self, *args, **options):
        # Find all records where record_id is NULL, ordered by creation time
        records_to_update = TestRecord.objects.filter(record_id__isnull=True).order_by('created_at')
        count = records_to_update.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All records already have a record_id. Nothing to do.'))
            return

        self.stdout.write(f'Found {count} records to update...')

        # This dictionary will keep track of the last sequence number used for each day
        daily_sequences = {}
        updated_count = 0

        for record in records_to_update:
            record_date = record.created_at.date()
            date_str = record_date.strftime('%Y%m%d')

            # If we haven't processed this day yet, we need to figure out the starting sequence
            if record_date not in daily_sequences:
                # Find the highest sequence number already in the DB for this day
                last_record_for_day = TestRecord.objects.filter(
                    created_at__date=record_date,
                    record_id__isnull=False
                ).order_by('-record_id').first()
                
                start_sequence = 0
                if last_record_for_day and last_record_for_day.record_id:
                    try:
                        start_sequence = int(last_record_for_day.record_id.split('-')[-1])
                    except (ValueError, IndexError):
                        pass # Keep sequence at 0
                
                daily_sequences[record_date] = start_sequence

            # Increment the sequence for the current day
            new_sequence = daily_sequences[record_date] + 1
            daily_sequences[record_date] = new_sequence # Update the tracker

            # Assign the new, unique ID
            record.record_id = f'TR-{date_str}-{new_sequence:04d}'
            record.save(update_fields=['record_id'])
            
            self.stdout.write(f'Successfully updated record (PK: {record.pk}) with new ID: {record.record_id}')
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated_count} records.'))