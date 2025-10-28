from rest_framework import serializers
from ..models import ParameterDefinition

class ParameterDefinitionLiteSerializer(serializers.ModelSerializer):
    """
    A lightweight, read-only serializer for displaying parameters in a list.
    """
    class Meta:
        model = ParameterDefinition
        fields = [
            "id",
            "name",
            "data_type",
            "unit",
            "is_required",
        ]