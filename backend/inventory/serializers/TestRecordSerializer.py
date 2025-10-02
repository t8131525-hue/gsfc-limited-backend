from rest_framework import serializers
from ..models import TestRecord, TestResult, Version
from .TestResultDisplaySerializer import TestResultDisplaySerializer
from .TestResultInputSerializer import TestResultInputSerializer
from django.db import transaction

class TestRecordSerializer(serializers.ModelSerializer):
    parameter_values = TestResultDisplaySerializer(many=True, read_only=True)
    results_input = TestResultInputSerializer(
        many=True, write_only=True, source="parameter_values"
    )
    analyst_username = serializers.CharField(source="analyst.username", read_only=True)
    
    # Corrected source to get product name via the version
    product_name = serializers.CharField(source="version.product.name", read_only=True)
    product_grade_name = serializers.CharField(
        source="product_grade.name", read_only=True, allow_null=True
    )
    lab_name = serializers.CharField(source="lab.name", read_only=True)
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
            "version",  # <-- Corrected from 'product'
            "product_grade",
            "sample_id",
            "batch_no",
            "status",
            "lab",
            "analyst",
            "analyst_username",
            "supervisor_comments",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "product_name",
            "product_grade_name",
             "lab_name", 
            "parameter_values",
            "results_input",
            "retest_record_id",
            "retests",
        ]
        read_only_fields = (
            "analyst",
            "approved_by",
            "approved_at",
            "retest_of",
        )
    
    def validate_version(self, value):
        """
        Check that the version is active.
        """
        if not value.is_active:
            raise serializers.ValidationError("Can only create test records for an active version.")
        return value

    # Your create and update methods are excellent and don't need changes,
    # but I've included them here for completeness.
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
            # This is a robust way to handle nested updates. Great job here.
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
        return instance

    def get_retests(self, obj):
        # This will return a list of record_ids for easier frontend use.
        return [r.record_id for r in obj.retests.all()]