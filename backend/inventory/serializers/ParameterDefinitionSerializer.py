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
        Your excellent validation method. No changes needed here.
        """
        # We need to build a complete instance to run full_clean
        instance = self.instance or ParameterDefinition()
        
        # Get related owner object for validation if creating
        if 'content_type' in data and 'object_id' in data:
            owner_model = data['content_type'].model_class()
            try:
                owner_instance = owner_model.objects.get(pk=data['object_id'])
                instance.owner = owner_instance
            except owner_model.DoesNotExist:
                 raise serializers.ValidationError("The specified owner does not exist.")

        # Apply the new data to the instance
        for attr, value in data.items():
            setattr(instance, attr, value)
            
        try:
            # This correctly runs your model's clean() method
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
            
        return data