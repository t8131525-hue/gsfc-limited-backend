from rest_framework import serializers
from ..models import ProductGrade
from .ParameterDefinitionLiteSerializer import ParameterDefinitionLiteSerializer

class ProductGradeLiteSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for grades nested inside a version.
    """
    parameters = ParameterDefinitionLiteSerializer(many=True, read_only=True)

    class Meta:
        model = ProductGrade
        fields = [
            "id",           # Needed for React keys
            "name",
            "description",
            "parameters",   # Now uses the LITE serializer
        ]