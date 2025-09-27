# inventory/serializers/SpecificationSerializer.py

from rest_framework import serializers
from ..models import Specification, ParameterDefinition
from .ParameterDisplaySerializer import ParameterDisplaySerializer


class SpecificationSerializer(serializers.ModelSerializer):
    # Read-only fields for displaying convenient names in the UI
    product_name = serializers.CharField(
        source="product.name", read_only=True, allow_null=True
    )
    product_grade_name = serializers.CharField(
        source="product_grade.name", read_only=True, allow_null=True
    )

    # For GET requests: Display nested parameter details using your lightweight serializer.
    parameters = ParameterDisplaySerializer(many=True, read_only=True)

    # For POST/PUT requests: Accept a list of parameter IDs to link.
    parameter_ids = serializers.PrimaryKeyRelatedField(
        queryset=ParameterDefinition.objects.all(),
        many=True,
        write_only=True,
        source="parameters", 
    )

    class Meta:
        model = Specification
        fields = [
            "id",
            "name",
            "version",
            "is_active",
            "product",  
            "product_grade", 
            "product_name",  
            "product_grade_name", 
            "parameters",  
            "parameter_ids",  
            "created_at",
            "activated_at",
        ]
        read_only_fields = ("version", "activated_at")

    def validate(self, data):
        # The model's clean method is automatically called by DRF,
        # so the logic you wrote there is already handled.
        return data
