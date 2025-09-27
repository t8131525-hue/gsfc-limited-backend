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
        source="parameters",  # This maps the input to the 'parameters' model field
    )

    class Meta:
        model = Specification
        fields = [
            "id",
            "name",
            "version",
            "is_active",
            "product",  # Used for writing (accepts a product ID)
            "product_grade",  # Used for writing (accepts a grade ID)
            "product_name",  # Used for reading
            "product_grade_name",  # Used for reading
            "parameters",  # The read-only, nested list of parameter details
            "parameter_ids",  # The write-only list of parameter IDs
            "created_at",
            "activated_at",
        ]
        read_only_fields = ("version", "activated_at")

    def validate(self, data):
        # The model's clean method is automatically called by DRF,
        # so the logic you wrote there is already handled.
        return data
