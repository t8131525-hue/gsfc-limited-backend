from rest_framework import serializers
from ..models import Product


class ProductListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for displaying products in a list view.
    Only includes essential fields for performance.
    """

    class Meta:
        model = Product
        fields = ["id", "product_id", "name"]
