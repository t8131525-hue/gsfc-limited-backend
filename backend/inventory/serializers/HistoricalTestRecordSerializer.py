# inventory/serializers/HistoricalTestRecordSerializer.py
from rest_framework import serializers
from ..models import TestRecord


class HistoricalTestRecordSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="version.product.name", read_only=True)
    lab_name = serializers.CharField(source="lab.name", read_only=True)

    analyst_full_name = serializers.SerializerMethodField()

    class Meta:
        model = TestRecord
        fields = [
            "id",
            "record_id",
            "product_name",
            "analyst_full_name",
            "created_at",
            "lab_name",
            "status",
        ]

    def get_analyst_full_name(self, obj):
        if obj.analyst:
            full_name = obj.analyst.get_full_name()
            return full_name if full_name else obj.analyst.username
        return None
