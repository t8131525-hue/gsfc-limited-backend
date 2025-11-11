from rest_framework import serializers
from ..models import Product
from .VersionNestedLiteSerializer import VersionNestedLiteSerializer


class ProductSerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()
    active_version_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "versions",
            "active_version_name",
        ]

    def get_active_version(self, obj):
        """Helper method to get the active version once."""
        if not hasattr(self, "_active_version"):
            self._active_version = obj.versions.filter(is_active=True).first()
        return self._active_version

    def get_active_version_name(self, obj):
        """Get the name from the active version."""
        active_version = self.get_active_version(obj)
        if active_version:
            return active_version.version_name
        return None

    def get_versions(self, obj):
        """
        This method is called by the 'versions' SerializerMethodField.
        It finds the single active version, serializes it,
        and returns it in a list.
        """
        active_version = self.get_active_version(obj)
        context = self.context

        if active_version:
            serializer = VersionNestedLiteSerializer(active_version, context=context)
            return [serializer.data]

        return []
