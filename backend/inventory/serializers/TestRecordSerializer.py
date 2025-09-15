from rest_framework import serializers
from ..serializers import TestResultDisplaySerializer, TestResultInputSerializer
from ..models import TestRecord, TestResult
from django.db import transaction
from audit_trail.utils import log_custom_event


class TestRecordSerializer(serializers.ModelSerializer):
    parameter_values = TestResultDisplaySerializer(many=True, read_only=True)
    results_input = TestResultInputSerializer(
        many=True, write_only=True, source="parameter_values"
    )
    analyst_username = serializers.CharField(source="analyst.username", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_grade_name = serializers.CharField(
        source="product_grade.name", read_only=True, allow_null=True
    )
    record_id = serializers.CharField(read_only=True)
    retest_record_id = serializers.CharField(
        source="retest_of.record_id", read_only=True
    )
    retests = serializers.SerializerMethodField()

    class Meta:
        model = TestRecord
        fields = [
            "id",
            "record_id",
            "retest_record_id",
            "retests",
            "product",
            "product_grade",
            "sample_id",
            "batch_no",
            "test_date",
            "status",
            "analyst",
            "analyst_username",
            "supervisor_comments",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "product_name",
            "product_grade_name",
            "parameter_values",
            "results_input",
        ]
        read_only_fields = (
            "analyst",
            "approved_by",
            "approved_at",
            "test_date",
            "retest_of",
        )

    @transaction.atomic
    def create(self, validated_data):
        parameter_values_data = validated_data.pop("parameter_values")
        validated_data["analyst"] = self.context["request"].user
        test_record = TestRecord.objects.create(**validated_data)
        for result_data in parameter_values_data:
            TestResult.objects.create(test_record=test_record, **result_data)
        return test_record

    @transaction.atomic
    def update(self, instance, validated_data):
        parameter_values_data = validated_data.pop("parameter_values", None)
        instance = super().update(instance, validated_data)
        if parameter_values_data is not None:
            existing_results = {
                result.parameter.id: result
                for result in instance.parameter_values.all()
            }
            for result_data in parameter_values_data:
                parameter = result_data["parameter"]
                if parameter.id in existing_results:
                    result_instance = existing_results.pop(parameter.id)
                    result_instance.value_decimal = result_data.get("value_decimal")
                    result_instance.value_string = result_data.get("value_string")
                    result_instance.value_boolean = result_data.get("value_boolean")
                    result_instance.save()
                else:
                    TestResult.objects.create(test_record=instance, **result_data)
            if existing_results:
                TestResult.objects.filter(
                    id__in=[res.id for res in existing_results.values()]
                ).delete()

        if instance.status == "PENDING_RETEST":
            instance.status = "PENDING"
            instance.save(update_fields=["status"])

            # Log this important status change
            log_custom_event(
                instance=instance,
                action_type="RESULTS_SUBMITTED",
                user=self.context["request"].user,
                details=f"Analyst submitted results for a retest. Status updated to PENDING.",
            )

        return instance

    def get_retests(self, obj):
        # This will return a list of primary keys, e.g., [8, 9]
        return [r.id for r in obj.retests.all()]
