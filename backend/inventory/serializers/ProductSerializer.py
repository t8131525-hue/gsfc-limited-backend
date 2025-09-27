from rest_framework import serializers
from .ProductGradeSerializer import ProductGradeSerializer
from inventory.models import Product
from .ParameterDefinitionSerializer import ParameterDefinitionSerializer


class ProductSerializer(serializers.ModelSerializer):
    grades = ProductGradeSerializer(many=True, read_only=True)
    parameters = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "description",
            "created_at",
            "updated_at",
            "grades",
            "parameters",
        ]

    def get_parameters(self, obj):
        """
        This method is called by the 'parameters' SerializerMethodField.
        It filters the related parameters to include only those directly
        linked to the product (where product_grade is null).
        'obj' is the Product instance.
        """
        direct_params = obj.parameters.filter(product_grade__isnull=True)
        # We use the ParameterDefinitionSerializer to serialize the filtered queryset.
        return ParameterDefinitionSerializer(direct_params, many=True).data
