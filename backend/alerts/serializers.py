# alerts/serializers.py
from rest_framework import serializers
from .models import Alert
from inventory.serializers import TestRecordForAlertContextSerializer


class AlertSerializer(serializers.ModelSerializer):
    """This serializer is for the main list view of alerts."""

    sample_id = serializers.CharField(source="test_record.sample_id", read_only=True)
    product_name = serializers.CharField(
        source="test_record.version.product.name", read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_id",
            "status",
            "details",
            "created_at",
            "sample_id",
            "product_name",
            "test_record",
        ]


class AlertContextSerializer(serializers.ModelSerializer):
    """
    This serializer powers the detail page. It nests the full test record
    context by using the serializer we imported from the inventory app.
    """

    test_record_data = TestRecordForAlertContextSerializer(
        source="test_record", read_only=True
    )
    product_name = serializers.CharField(
        source="test_record.version.product.name", read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_id",
            "status",
            "details",
            "created_at",
            "product_name",
            "test_record_data",
        ]
