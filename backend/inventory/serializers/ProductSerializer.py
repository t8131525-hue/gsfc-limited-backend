from rest_framework import serializers
from ..models import Product
# Make sure to import the new VersionNestedSerializer we defined above
from .VersionNestedSerializer import VersionNestedSerializer # Adjust the import path as needed


class ProductSerializer(serializers.ModelSerializer):
    # This correctly uses the related_name 'versions' from your Product model
    # and our new nested serializer.
    versions = VersionNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_id",
            "description",
            "versions", # Display the nested versions instead of grades/parameters
            "created_at",
            "updated_at",
        ]

    # The old 'grades' and 'parameters' fields and the 'get_parameters' method
    # are no longer needed and should be removed.