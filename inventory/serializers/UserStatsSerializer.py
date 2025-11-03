# inventory/serializers/UserStatsSerializer.py

from rest_framework import serializers


class UserPerformanceSerializer(serializers.Serializer):
    """
    Serializes aggregated data for the user performance chart.
    e.g., {"date": "2025-10-01", "count": 15}
    """

    date = serializers.DateField()
    count = serializers.IntegerField()


class UserSummaryCountsSerializer(serializers.Serializer):
    """
    Serializes the summary counts for a user's activity.
    """

    count_today = serializers.IntegerField()
    count_week = serializers.IntegerField()
    count_month = serializers.IntegerField()
    count_3_months = serializers.IntegerField()
    count_6_months = serializers.IntegerField()
    count_year = serializers.IntegerField()
    count_custom = serializers.IntegerField(required=False)
