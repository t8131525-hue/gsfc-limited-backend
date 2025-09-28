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
        # If updating, use the existing instance.
        # If creating, create a new instance WITH the incoming data.
        instance = self.instance or Version(**data)
        
        # If updating, we still need to apply the changes before cleaning.
        if self.instance:
            for attr, value in data.items():
                setattr(instance, attr, value)
        
        try:
            # This now runs on an instance that has a 'product' attribute.
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
            
        return data