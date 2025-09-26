from rest_framework import serializers
from .ProductGradeSerializer import ProductGradeSerializer
from inventory.models import Product
from .ParameterDefinitionSerializer import ParameterDefinitionSerializer



class ProductSerializer(serializers.ModelSerializer):
    grades = ProductGradeSerializer(many=True, read_only=True)
    parameters = ParameterDefinitionSerializer(
        source="parameters.filter(product_grade__isnull=True)", many=True, read_only=True
    )
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "description",
            "created_at",
            "updated_at",
            "grades", # This will now contain the grades AND their nested 
            "parameters"
        ]