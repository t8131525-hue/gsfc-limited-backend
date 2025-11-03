from rest_framework import serializers
from ..models import ParameterDefinition


class ParameterDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterDefinition
        fields = ["name", "unit", "min_value", "max_value", "data_type"]
