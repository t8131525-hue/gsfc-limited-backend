from rest_framework import serializers
from ..models import Product, TestRecord, ParameterDefinition, ProductGrade


# A serializer for the aggregated trend data (avg, min, max)
class AggregatedDataPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    avg = serializers.FloatField()
    min = serializers.FloatField()
    max = serializers.FloatField()


# A serializer for a single parameter's trend line
class AggregatedTrendSerializer(serializers.ModelSerializer):
    data_points = AggregatedDataPointSerializer(many=True, read_only=True)

    class Meta:
        model = ParameterDefinition
        fields = ["id", "name", "unit", "min_value", "max_value", "data_points"]


class GradeWithTrendsSerializer(serializers.ModelSerializer):
    trends = AggregatedTrendSerializer(many=True, read_only=True)

    class Meta:
        model = ProductGrade
        fields = ["id", "name", "trends"]


# A lightweight serializer for the recent tests table
class RecentTestRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestRecord
        fields = ["id", "record_id", "status", "created_at"]


# The main serializer that combines all data for the page
class ProductQualityDetailSerializer(serializers.ModelSerializer):
    active_version_name = serializers.CharField(
        source="active_version.version_name", read_only=True
    )
    trends = AggregatedTrendSerializer(many=True, read_only=True)
    grades = GradeWithTrendsSerializer(many=True, read_only=True)
    recent_tests = RecentTestRecordSerializer(many=True, read_only=True)
    has_grades = serializers.BooleanField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "active_version_name",
            "has_grades",
            "grades",
            "trends",
            "recent_tests",
        ]
