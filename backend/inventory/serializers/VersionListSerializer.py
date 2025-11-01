from rest_framework import serializers
from ..models import Version


class VersionListSerializer(serializers.ModelSerializer):
    """
    A lightweight, read-only serializer for displaying versions in a list.
    """

    class Meta:
        model = Version
        fields = [
            "id",
            "version_name",
            "status",
            "is_active",
        ]
        read_only_fields = fields
