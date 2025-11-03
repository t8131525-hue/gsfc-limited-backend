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
            "enum_options",
            "min_value",
            "max_value",
            "boolean_true_label",
            "boolean_false_label",
        ]
