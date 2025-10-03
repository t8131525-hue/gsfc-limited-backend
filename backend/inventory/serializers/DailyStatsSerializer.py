# inventory/serializers/DailyStatsSerializer.py

from rest_framework import serializers

class DailyStatsSerializer(serializers.Serializer):
    """
    A simple serializer for returning aggregated daily test record stats.
    """
    total_tests = serializers.IntegerField()
    pending_tests = serializers.IntegerField()
    approved_tests = serializers.IntegerField()
    rejected_tests = serializers.IntegerField()