from rest_framework import serializers
from ..models import ParameterDefinition, Version, ProductGrade
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.contenttypes.models import ContentType


class ParameterDefinitionSerializer(serializers.ModelSerializer):
    # This field will dynamically show who the parameter belongs to.
    owner_info = serializers.SerializerMethodField()

    class Meta:
        model = ParameterDefinition
        # We explicitly list fields to control the order and exclude old ones.
        fields = [
            'id', 'owner_info', 'name', 'description', 'data_type', 
            'unit', 'is_required', 'enum_options', 'min_value', 
            'max_value', 'boolean_true_label', 'boolean_false_label',
            'content_type', 'object_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ("created_at", "updated_at", "owner_info")
        # These fields are required for writing but not for reading.
        extra_kwargs = {
            'content_type': {'write_only': True},
            'object_id': {'write_only': True},
        }

    def get_owner_info(self, obj):
        """
        Checks the type of the owner and returns a descriptive dictionary.
        """
        if isinstance(obj.owner, Version):
            return {
                "owner_type": "Version",
                "product": obj.owner.product.name,
                "version_name": obj.owner.version_name,
            }
        if isinstance(obj.owner, ProductGrade):
            return {
                "owner_type": "ProductGrade",
                "product": obj.owner.version.product.name,
                "version_name": obj.owner.version.version_name,
                "grade_name": obj.owner.name,
            }
        return None

    def validate(self, data):
        """
        Runs the model's validation on a fully populated instance.
        """
        # If updating, use the existing instance.
        # If creating, create a new instance WITH the incoming data.
        instance = self.instance or ParameterDefinition(**data)
        
        # If updating, apply changes to the instance before cleaning.
        if self.instance:
            for attr, value in data.items():
                setattr(instance, attr, value)
        
        try:
            # This now runs on an instance that has the necessary related fields.
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
            
        return data