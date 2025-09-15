from rest_framework import serializers
from inventory.serializers.ProductGradeSerializer import ProductGradeSerializer
from inventory.models import Product


class ProductSerializer(serializers.ModelSerializer):
    grades = ProductGradeSerializer(many=True, read_only=True)

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
        ]
        read_only_fields = ("created_at", "updated_at", "product_id")
