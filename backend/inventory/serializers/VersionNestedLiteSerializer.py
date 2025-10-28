from rest_framework import serializers
from ..models import Version
from .ProductGradeLiteSerializer import ProductGradeLiteSerializer
from .ParameterDefinitionLiteSerializer import ParameterDefinitionLiteSerializer

class VersionNestedLiteSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for the active version nested in a product.
    """
    parameters = ParameterDefinitionLiteSerializer(
        many=True, 
        read_only=True, 
        source="parameters.all"
    )
    grades = ProductGradeLiteSerializer(many=True, read_only=True)

    class Meta:
        model = Version
        fields = [
            'id',
            'version_name',
            'description',
            'parameters',     
            'grades',
            'is_active',
        ]