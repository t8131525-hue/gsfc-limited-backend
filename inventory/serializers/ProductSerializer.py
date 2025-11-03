from rest_framework import serializers
from ..models import Product
from .VersionNestedLiteSerializer import VersionNestedLiteSerializer


class ProductSerializer(serializers.ModelSerializer):

    versions = serializers.SerializerMethodField()
    active_version_name = serializers.CharField(
        source="active_version.version_name", read_only=True, default=None
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "versions",
            "active_version_name",
        ]

    def get_versions(self, obj):
        """
        This method is called by the 'versions' SerializerMethodField.
        It finds the single active version, serializes it,
        and returns it in a list.
        """
        active_version = obj.versions.filter(is_active=True).first()
        context = self.context

        if active_version:
            serializer = VersionNestedLiteSerializer(active_version, context=context)
            return [serializer.data]

        return []