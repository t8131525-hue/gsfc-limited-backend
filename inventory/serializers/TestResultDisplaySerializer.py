from rest_framework import serializers
from ..models import TestResult
from ..serializers.ParameterDisplaySerializer import ParameterDisplaySerializer
from decimal import Decimal


class TestResultDisplaySerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying a single test result in context."""

    parameter = ParameterDisplaySerializer(read_only=True)
    display_value = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = ["id", "parameter", "display_value", "status"]

    def get_display_value(self, obj: TestResult) -> any:
        if obj.value_decimal is not None:
            return float(obj.value_decimal)
        if obj.value_string is not None:
            return obj.value_string
        if obj.value_boolean is not None:
            param_def = obj.parameter
            if param_def.boolean_true_label and param_def.boolean_false_label:
                return (
                    param_def.boolean_true_label
                    if obj.value_boolean
                    else param_def.boolean_false_label
                )
            return "Yes" if obj.value_boolean else "No"
        return None

    def get_status(self, obj: TestResult) -> str:
        param_def = obj.parameter
        value = self.get_display_value(obj)
        if param_def.data_type in ["INTEGER", "DECIMAL"] and value is not None:
            min_val = param_def.min_value
            max_val = param_def.max_value
            if min_val is not None and max_val is not None:
                if not (min_val <= Decimal(str(value)) <= max_val):
                    return "OUT_OF_SPEC"
        return "IN_SPEC"
