from rest_framework import serializers
from ..models import Version
from django.core.exceptions import ValidationError as DjangoValidationError

class VersionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Version
        fields = [
            'id', 'product', 'product_name', 'version_name', 'description', 
            'status', 'is_active', 'created_by', 'created_by_username',
            'created_at', 'locked_at', 'activated_at'
        ]
        read_only_fields = ('status', 'is_active', 'created_by', 'locked_at', 'activated_at', 'created_at')

    def validate(self, data):
        """
        Runs the model's clean method to enforce business logic.
        """
        # Build an instance to run the model's validation
        instance = self.instance or Version()
        # Apply the new data to the instance
        for attr, value in data.items():
            setattr(instance, attr, value)

        try:
            # This correctly runs your model's clean() method
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
            
        return data