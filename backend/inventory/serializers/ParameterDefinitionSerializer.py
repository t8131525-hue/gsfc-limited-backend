from rest_framework import serializers
from ..models import ParameterDefinition
from django.core.exceptions import ValidationError as DjangoValidationError


class ParameterDefinitionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_grade_name = serializers.CharField(
        source="product_grade.name", read_only=True
    )

    class Meta:
        model = ParameterDefinition
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate(self, data):
        instance = self.instance or ParameterDefinition()
        for attr, value in data.items():
            setattr(instance, attr, value)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data
