from rest_framework import serializers
from ..models import ParameterDefinition, Version, ProductGrade
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.contenttypes.models import ContentType


class ParameterDefinitionSerializer(serializers.ModelSerializer):
    owner_info = serializers.SerializerMethodField()

    # ✅ 1. Add these write-only fields to accept a direct ID
    version_id = serializers.IntegerField(write_only=True, required=False)
    grade_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ParameterDefinition
        fields = [
            "id",
            "owner_info",
            "name",
            "description",
            "data_type",
            "unit",
            "is_required",
            "enum_options",
            "min_value",
            "max_value",
            "boolean_true_label",
            "boolean_false_label",
            "version_id",
            "grade_id",
        ]
        read_only_fields = ("owner_info",)

    def get_owner_info(self, obj):
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
        if not self.instance:  # Only on create
            if "version_id" not in data and "grade_id" not in data:
                raise serializers.ValidationError(
                    "Either a 'version_id' or a 'grade_id' must be provided."
                )
            if "version_id" in data and "grade_id" in data:
                raise serializers.ValidationError(
                    "Provide either a 'version_id' or a 'grade_id', not both."
                )
        return data

    def create(self, validated_data):
        version_id = validated_data.pop("version_id", None)
        grade_id = validated_data.pop("grade_id", None)

        owner_object = None
        if version_id:
            try:
                owner_object = Version.objects.get(pk=version_id)
            except Version.DoesNotExist:
                raise serializers.ValidationError({"version_id": "Version not found."})

        elif grade_id:
            try:
                owner_object = ProductGrade.objects.get(pk=grade_id)
            except ProductGrade.DoesNotExist:
                raise serializers.ValidationError(
                    {"grade_id": "ProductGrade not found."}
                )

        # --- FIX: Wrap the create() call in a try/except ---
        try:
            parameter = ParameterDefinition.objects.create(
                owner=owner_object, **validated_data
            )
            return parameter
        except DjangoValidationError as e:
            # Catch the validation error from model.save() -> full_clean()
            raise serializers.ValidationError(e.message_dict)
        # --- END FIX ---
