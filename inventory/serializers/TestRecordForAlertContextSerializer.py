from rest_framework import serializers
from .TestResultDisplaySerializer import TestResultDisplaySerializer
from ..models import TestRecord


class TestRecordForAlertContextSerializer(serializers.ModelSerializer):
    results = TestResultDisplaySerializer(
        many=True, read_only=True, source="parameter_values"
    )

    class Meta:
        model = TestRecord
        fields = ["id", "sample_id", "created_at", "status", "results"]
