from rest_framework import serializers
from ..models import ProductGrade
from django.core.exceptions import ValidationError as DjangoValidationError


class ProductGradeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductGrade
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate(self, data):
        instance = ProductGrade(**data)
        try:
            queryset = ProductGrade.objects.filter(
                product=data.get("product"), name=data.get("name")
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": f"A grade with this name already exists for this product."}
                )
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data
