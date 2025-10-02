# inventory/serializers/RecentTestRecordSerializer.py

from rest_framework import serializers
from ..models import TestRecord

class RecentTestRecordSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for displaying a list of test records created today.
    """
    product_name = serializers.CharField(source="version.product.name", read_only=True)
    analyst_username = serializers.CharField(source="analyst.username", read_only=True, allow_null=True)
    lab_name = serializers.CharField(source="lab.name", read_only=True)

    class Meta:
        model = TestRecord
        fields = [
            'id',
            'record_id',
            'product_name',
            'analyst_username',
            'created_at',
            'lab_name',
            'status',
        ]