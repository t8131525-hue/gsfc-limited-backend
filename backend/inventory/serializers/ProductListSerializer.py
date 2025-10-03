from rest_framework import serializers
from ..models import Product

class ProductListSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for displaying products in a list view.
    Only includes essential fields for performance.
    """
    active_version_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'product_id', 'name', 'created_at', 
            'active_version_name' 
        ]

    def get_active_version_name(self, obj):
        active_version = obj.versions.filter(is_active=True).first()
        return active_version.version_name if active_version else None