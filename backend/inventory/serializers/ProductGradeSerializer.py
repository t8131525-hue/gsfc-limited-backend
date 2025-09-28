from rest_framework import serializers
from ..models import ProductGrade
from .ParameterDefinitionSerializer import ParameterDefinitionSerializer


class ProductGradeSerializer(serializers.ModelSerializer):
    # This correctly nests the parameters that belong to this grade.
    parameters = ParameterDefinitionSerializer(many=True, read_only=True)
    # This provides the name of the product for context.
    product_name = serializers.CharField(source="version.product.name", read_only=True)

    class Meta:
        model = ProductGrade
        fields = [
            "id",
            "version",  # The grade must be linked to a Version
            "product_name",
            "name",
            "description",
            "parameters",
        ]

    # We no longer need the custom 'validate' method.
    # The 'unique_together' on the model is enough for DRF to validate uniqueness.
