# alerts/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from inventory.models import Product, ParameterDefinition, TestRecord, TestResult
from .models import Alert
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

User = get_user_model()

class AlertsTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product for Alerts")
        self.parameter = ParameterDefinition.objects.create(
            product=self.product,
            name="Viscosity",
            data_type="DECIMAL",
            min_value=Decimal('2.4'),
            max_value=Decimal('2.6')
        )
        self.test_record = TestRecord.objects.create(
            product=self.product,
            sample_id="ALERT-SAMPLE-001",
            batch_no="BATCH-A"
        )
        self.client = APIClient()

    def test_alert_is_created_for_out_of_range_value(self):
        """
        Ensure an Alert is automatically created when a TestResult is saved with a value
        that is outside the ParameterDefinition's normal range.
        """
        self.assertEqual(Alert.objects.count(), 0)

        TestResult.objects.create(
            test_record=self.test_record,
            parameter=self.parameter,
            value_decimal=Decimal('2.8')
        )

        self.assertEqual(Alert.objects.count(), 1)
        
        alert = Alert.objects.first()
        self.assertEqual(alert.status, 'NEW')
        self.assertEqual(alert.test_record, self.test_record)
        self.assertEqual(alert.details['value_entered'], 2.8)

    def test_alert_is_not_created_for_in_range_value(self):
        """
        Ensure an Alert is NOT created when a TestResult value is within the normal range.
        """
        self.assertEqual(Alert.objects.count(), 0)

        TestResult.objects.create(
            test_record=self.test_record,
            parameter=self.parameter,
            value_decimal=Decimal('2.5')
        )

        self.assertEqual(Alert.objects.count(), 0)

    def test_alert_api_endpoint_is_public_and_returns_data(self):
        """
        Ensure the /api/alerts/ endpoint is public and returns alert data correctly.
        """
        TestResult.objects.create(
            test_record=self.test_record,
            parameter=self.parameter,
            value_decimal=Decimal('3.0')
        )
        self.assertEqual(Alert.objects.count(), 1)

        response = self.client.get('/api/alerts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # --- FIX: Access the response data as a list ---
        self.assertEqual(len(response.data), 1)
        alert_data = response.data[0]
        # --- End of fix ---

        self.assertEqual(alert_data['status'], 'NEW')
        self.assertEqual(alert_data['sample_id'], 'ALERT-SAMPLE-001')
        self.assertEqual(alert_data['details']['value_entered'], 3.0)