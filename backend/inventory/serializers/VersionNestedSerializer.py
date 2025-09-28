# This is a new serializer class
from rest_framework import serializers
from ..models import Version
from .ProductGradeSerializer import ProductGradeSerializer
from .ParameterDefinitionSerializer import ParameterDefinitionSerializer

class VersionNestedSerializer(serializers.ModelSerializer):
    """
    A read-only serializer to display version details nested within a Product.
    """
    # Nests the parameters that are directly on the version
    parameters = ParameterDefinitionSerializer(many=True, read_only=True)
    # Nests the grades that are on the version
    grades = ProductGradeSerializer(many=True, read_only=True)

    class Meta:
        model = Version
        fields = [
            'id', 'version_name', 'status', 'is_active', 
            'description', 'parameters', 'grades'
        ]