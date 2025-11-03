# inventory/serializers/QualityTrendSerializer.py

from rest_framework import serializers
from ..models import ParameterDefinition


class QualityTrendDataPointSerializer(serializers.Serializer):
    """Serializer for a single data point in the trend graph."""

    date = serializers.DateTimeField(source="created_at")
    value = serializers.DecimalField(
        max_digits=10, decimal_places=4, source="value_decimal"
    )


class QualityTrendSerializer(serializers.ModelSerializer):
    """
    Main serializer to structure the quality trend data for a parameter.
    It includes the parameter's details, its min/max limits, and its data points.
    """

    data_points = QualityTrendDataPointSerializer(many=True, read_only=True)

    class Meta:
        model = ParameterDefinition
        fields = [
            "id",
            "name",
            "unit",
            "min_value",
            "max_value",
            "data_points",
        ]
