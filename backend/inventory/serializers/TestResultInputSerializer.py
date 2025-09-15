from rest_framework import serializers
from ..models import ParameterDefinition, TestResult
from decimal import Decimal, ROUND_HALF_UP


class TestResultInputSerializer(serializers.ModelSerializer):
    parameter = serializers.PrimaryKeyRelatedField(
        queryset=ParameterDefinition.objects.all()
    )
    value = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = TestResult
        fields = ["parameter", "value"]

    def validate(self, data):
        parameter = data.get("parameter")
        value = data.get("value")
        if parameter and parameter.is_required and value is None:
            raise serializers.ValidationError(
                {"value": f"A value is required for '{parameter.name}'."}
            )
        if value is not None:
            if parameter.data_type in ["INTEGER", "DECIMAL"]:
                try:
                    data["value_decimal"] = Decimal(str(value)).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )
                except Exception:
                    raise serializers.ValidationError(
                        {"value": "A valid number is required."}
                    )
            elif parameter.data_type == "BOOLEAN":
                if not isinstance(value, bool):
                    raise serializers.ValidationError(
                        {"value": "A boolean (true/false) is required."}
                    )
                data["value_boolean"] = value
            else:
                if (
                    parameter.data_type == "ENUM"
                    and parameter.enum_options
                    and str(value) not in parameter.enum_options
                ):
                    raise serializers.ValidationError(
                        {"value": f"Value must be one of: {parameter.enum_options}"}
                    )
                data["value_string"] = str(value)
        if "value" in data:
            data.pop("value")
        return data
