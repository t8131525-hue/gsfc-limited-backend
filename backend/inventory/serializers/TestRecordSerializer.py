from rest_framework import serializers
from ..models import TestRecord, TestResult, Version
from alerts.models import Alert
from .TestResultDisplaySerializer import TestResultDisplaySerializer
from .TestResultInputSerializer import TestResultInputSerializer
from django.db import transaction


class RelatedTestRecordSerializer(serializers.ModelSerializer):
    """A lightweight serializer for related test records."""

    class Meta:
        model = TestRecord
        fields = ["id", "record_id"]


class RelatedAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["id", "alert_id"]


class TestRecordSerializer(serializers.ModelSerializer):
    parameter_values = TestResultDisplaySerializer(many=True, read_only=True)
    results_input = TestResultInputSerializer(
        many=True, write_only=True, source="parameter_values"
    )
    analyst_full_name = serializers.SerializerMethodField()
    approved_by_full_name = serializers.SerializerMethodField()
    closed_by_full_name = serializers.SerializerMethodField()
    retest_ordered_by_full_name = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="version.product.name", read_only=True)
    product_grade_name = serializers.CharField(
        source="product_grade.name", read_only=True, allow_null=True
    )
    lab_name = serializers.CharField(source="lab.name", read_only=True)
    record_id = serializers.CharField(read_only=True)

    retest_of = RelatedTestRecordSerializer(read_only=True)
    retests = RelatedTestRecordSerializer(many=True, read_only=True)
    alerts = RelatedAlertSerializer(many=True, read_only=True)
    # alert_ids = serializers.SerializerMethodField()

    class Meta:
        model = TestRecord
        fields = [
            "id",
            "record_id",
            "version",
            "product_grade",
            "sample_id",
            "batch_no",
            "status",
            "lab",
            "analyst",
            "analyst_full_name",
            "supervisor_comments",
            "approved_by",
            "approved_by_full_name",
            "approved_at",
            "closed_by",
            "closed_at",
            "closed_by_full_name",
            "created_at",
            "retest_ordered_by",
            "retest_ordered_at",
            "retest_ordered_by_full_name",
            "updated_at",
            "product_name",
            "product_grade_name",
            "lab_name",
            "parameter_values",
            "results_input",
            "retest_of",
            "retests",
            # "alert_ids",
            "alerts",
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
            raise serializers.ValidationError(
                "Can only create test records for an active version."
            )
        return value

    def get_user_display_name(self, user):
        """Helper to get full name, falling back to username."""
        if not user:
            return None
        full_name = user.get_full_name()
        return full_name if full_name else user.username

    def get_analyst_full_name(self, obj):
        return self.get_user_display_name(obj.analyst)

    def get_approved_by_full_name(self, obj):
        return self.get_user_display_name(obj.approved_by)

    def get_closed_by_full_name(self, obj):
        return self.get_user_display_name(obj.closed_by)

    def get_retest_ordered_by_full_name(self, obj):
        return self.get_user_display_name(obj.retest_ordered_by)

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
        return instance

    # def get_retests(self, obj):
    #     # This will return a list of record_ids for easier frontend use.
    #     return [r.record_id for r in obj.retests.all()]

    # def get_alert_ids(self, obj):
    #     # This will return a list of alert IDs, e.g., ["AL-20251004-01"]
    #     return [alert.alert_id for alert in obj.alerts.all() if alert.alert_id]
