from rest_framework import serializers
from ..models import Product
from .VersionNestedSerializer import VersionNestedSerializer # Adjust the import path as needed


class ProductSerializer(serializers.ModelSerializer):
    versions = VersionNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "description",
            "versions", 
            "created_at",
            "updated_at",
        ]