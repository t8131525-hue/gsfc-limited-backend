from rest_framework import serializers
from ..models import Product

class ProductSelectSerializer(serializers.ModelSerializer):
    """
    An ultra-lightweight serializer for product selection dropdowns.
    Only includes the fields necessary to identify and select a product.
    """
    class Meta:
        model = Product
        fields = ['id', 'product_id', 'name']