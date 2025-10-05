import random
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP 
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import Group
from authentication.models import User
from inventory.models import (
    Lab,
    Product,
    Version,
    ParameterDefinition,
    TestRecord,
    TestResult,
)


class Command(BaseCommand):
    help = (
        "Populates the database with realistic historical test data for the last year."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing generated data before populating.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting data population script...")

        if options["clean"]:
            self.stdout.write("Cleaning up old generated data...")
            User.objects.filter(username__startswith="analyst_").delete()
            Product.objects.filter(name="Nylon 6").delete()
            Lab.objects.filter(name="Historical Data Lab").delete()
            self.stdout.write("Cleanup complete.")

        # --- 1. Create Users, Group, and Lab ---
        self.stdout.write("Creating Lab, Analyst Group, and Users...")
        lab, _ = Lab.objects.get_or_create(name="Historical Data Lab")
        analyst_group, _ = Group.objects.get_or_create(name="Analyst")

        analyst_names = [
            ("Rohan", "Sharma"),
            ("Priya", "Patel"),
            ("Amit", "Singh"),
            ("Sneha", "Gupta"),
            ("Vikram", "Kumar"),
        ]
        analysts = []
        for first, last in analyst_names:
            username = f"analyst_{first.lower()}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@example.com",
                },
            )
            if created:
                user.set_password("password123")
                user.save()
            user.groups.add(analyst_group)
            analysts.append(user)

        # --- 2. Create Product, Version, and Parameters ---
        self.stdout.write("Creating Product, Version, and Parameters for Nylon 6...")
        product, _ = Product.objects.get_or_create(
            name="Nylon 6",
            defaults={"description": "A common engineering thermoplastic."},
        )

        version, created = Version.objects.get_or_create(
            product=product,
            version_name="N6-Standard-2024",
            defaults={
                "description": "Standard testing specification for Nylon 6 in 2024."
            },
        )

        # Only add parameters if the version was just created
        if created:
            # ✅ FIX: Change the numeric values to strings for precise decimals.
            parameters_data = [
                {
                    "name": "Relative Viscosity (RV)",
                    "data_type": "DECIMAL",
                    "min_value": "2.40",
                    "max_value": "2.60",
                },
                {
                    "name": "Moisture Content",
                    "unit": "%",
                    "data_type": "DECIMAL",
                    "max_value": "0.10",
                },
                {
                    "name": "Extractable Content",
                    "unit": "%",
                    "data_type": "DECIMAL",
                    "max_value": "0.60",
                },
                {
                    "name": "Amine End Groups (NH2)",
                    "unit": "meq/kg",
                    "data_type": "INTEGER",
                    "min_value": 35,
                    "max_value": 55,
                },
                {
                    "name": "Carboxyl End Groups (COOH)",
                    "unit": "meq/kg",
                    "data_type": "INTEGER",
                    "min_value": 40,
                    "max_value": 60,
                },
            ]
            for param_data in parameters_data:
                ParameterDefinition.objects.create(owner=version, **param_data)

        # --- 3. Lock and Activate the Version ---
        self.stdout.write("Locking and activating the version...")
        version.status = "LOCKED"
        version.is_active = True
        version.save()

        # --- 4. Generate Historical Test Records for the Past Year ---
        self.stdout.write("Generating historical test records for the past 365 days...")
        today = timezone.now()
        for i in range(365):
            # Go back in time day by day
            current_date = today - timedelta(days=i)
            
            date_str = current_date.strftime('%Y%m%d')
            last_record_on_date = TestRecord.objects.filter(record_id__startswith=f"TR-{date_str}").order_by('-record_id').first()
            
            sequence = 1
            if last_record_on_date:
                try:
                    sequence = int(last_record_on_date.record_id.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    pass # Fallback to 1 if parsing fails

            # Randomly decide to create 1 to 5 records for this day
            if random.random() < 0.8:  # 80% chance to have records on a given day
                num_records_for_day = random.randint(1, 5)
                for _ in range(num_records_for_day):
                    # Pick a random analyst
                    analyst = random.choice(analysts)
                    final_status = random.choice(["CLOSED", "APPROVED"])

                    record_id = f"TR-{date_str}-{sequence:02d}"
                    sequence += 1 

                     # --- START OF THE FIX: Perform saves in sequential steps ---

                    # Step 1: Create the record in the initial PENDING state.
                    record = TestRecord.objects.create(
                        record_id=record_id,
                        version=version,
                        lab=lab,
                        batch_no=f"B{current_date.strftime('%Y%m%d')}-{random.randint(100, 999)}",
                        sample_id=f"S{random.randint(1000, 9999)}",
                        status="PENDING",
                        analyst=analyst,
                    )
                    
                    # Step 2: Back-date the creation timestamp. This is a safe, isolated update.
                    record.created_at = current_date
                    record.save(update_fields=['created_at'])

                    # Step 3: Now that the record exists with a past date, move it to APPROVED.
                    # This simulates a supervisor approving a pending record.
                    record.status = "APPROVED"
                    record.approved_at = current_date + timedelta(minutes=random.randint(30, 120))
                    record.save(update_fields=['status', 'approved_at'])

                    # Step 4: If the final desired status is CLOSED, perform one last update.
                    # This simulates a manager closing an approved record.
                    if final_status == "CLOSED":
                        record.status = "CLOSED"
                        record.closed_at = record.approved_at + timedelta(hours=random.randint(1, 24))
                        record.save(update_fields=['status', 'closed_at'])
                    
                    # --- END OF THE FIX ---



                    # Create results for this record
                    for param_def in version.parameters.all():
                        in_spec = random.random() < 0.9  # 90% chance to be in-spec
                        value = None

                        if param_def.data_type in ['DECIMAL', 'INTEGER']:
                            # Convert boundaries to Decimal for precise math
                            min_v = Decimal(str(param_def.min_value or '0.0'))
                            max_v = Decimal(str(param_def.max_value or '100.0'))
                            
                            if in_spec:
                                # Generate a random Decimal between min_v and max_v
                                rand_decimal = min_v + (max_v - min_v) * Decimal(str(random.random()))
                            else: # Out of spec
                                upper_bound = max_v * Decimal('1.2')
                                rand_decimal = max_v + (upper_bound - max_v) * Decimal(str(random.random()))

                            if param_def.data_type == 'DECIMAL':
                                # Precisely quantize the Decimal to 4 places
                                value = rand_decimal.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                            elif param_def.data_type == 'INTEGER':
                                value = int(rand_decimal) # Convert to in

                        TestResult.objects.create(
                            test_record=record,
                            parameter=param_def,
                            value_decimal=(
                                value
                                if param_def.data_type in ["DECIMAL", "INTEGER"]
                                else None
                            ),
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully populated the database with historical data!"
            )
        )
