from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Product, ProductGrade, ParameterDefinition, TestRecord, TestResult
from decimal import Decimal, ROUND_HALF_UP
from audit_trail.utils import log_custom_event 

User = get_user_model()

# This serializer is used by TestResultDisplaySerializer, so it must be defined first.
class ParameterDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterDefinition
        fields = ['name', 'unit','min_value', 'max_value', 'data_type']

# This serializer is used by ProductSerializer, so it must be defined before it.
class ProductGradeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = ProductGrade
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        instance = ProductGrade(**data)
        try:
            queryset = ProductGrade.objects.filter(product=data.get('product'), name=data.get('name'))
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({"name": f"A grade with this name already exists for this product."})
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data

class ProductSerializer(serializers.ModelSerializer):
    grades = ProductGradeSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'product_id', 'description', 'created_at', 'updated_at', 'grades']
        read_only_fields = ('created_at', 'updated_at', 'product_id')

class ParameterDefinitionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_grade_name = serializers.CharField(source='product_grade.name', read_only=True)
    class Meta:
        model = ParameterDefinition
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        instance = self.instance or ParameterDefinition()
        for attr, value in data.items():
            setattr(instance, attr, value)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data

class TestResultInputSerializer(serializers.ModelSerializer):
    parameter = serializers.PrimaryKeyRelatedField(queryset=ParameterDefinition.objects.all())
    value = serializers.JSONField(write_only=True, required=False)
    class Meta:
        model = TestResult
        fields = ['parameter', 'value']

    def validate(self, data):
        parameter = data.get('parameter')
        value = data.get('value')
        if parameter and parameter.is_required and value is None:
            raise serializers.ValidationError({"value": f"A value is required for '{parameter.name}'."})
        if value is not None:
            if parameter.data_type in ['INTEGER', 'DECIMAL']:
                try:
                    data['value_decimal'] = Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                except Exception:
                    raise serializers.ValidationError({'value': 'A valid number is required.'})
            elif parameter.data_type == 'BOOLEAN':
                if not isinstance(value, bool):
                    raise serializers.ValidationError({'value': 'A boolean (true/false) is required.'})
                data['value_boolean'] = value
            else:
                if parameter.data_type == 'ENUM' and parameter.enum_options and str(value) not in parameter.enum_options:
                    raise serializers.ValidationError({'value': f"Value must be one of: {parameter.enum_options}"})
                data['value_string'] = str(value)
        if 'value' in data:
            data.pop('value')
        return data

# This serializer is used by TestRecordSerializer, so it must be defined before it.
class TestResultDisplaySerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying a single test result in context."""
    parameter = ParameterDisplaySerializer(read_only=True)
    # --- FIX 1: Rename 'value' back to 'display_value' ---
    display_value = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField() 

    class Meta:
        model = TestResult
        # --- FIX 2: Update the fields list ---
        fields = ['id', 'parameter', 'display_value', 'status']

    # --- FIX 3: Rename 'get_value' back to 'get_display_value' ---
    def get_display_value(self, obj: TestResult) -> any:
        if obj.value_decimal is not None:
            return float(obj.value_decimal)
        if obj.value_string is not None:
            return obj.value_string
        if obj.value_boolean is not None:
            # Display the custom labels if they exist, otherwise default to Yes/No
            param_def = obj.parameter
            if param_def.boolean_true_label and param_def.boolean_false_label:
                return param_def.boolean_true_label if obj.value_boolean else param_def.boolean_false_label
            return "Yes" if obj.value_boolean else "No"
        return None
    
    def get_status(self, obj: TestResult) -> str:
        param_def = obj.parameter
        value = self.get_display_value(obj) # Use the corrected method name
        if param_def.data_type in ['INTEGER', 'DECIMAL'] and value is not None:
            min_val = param_def.min_value
            max_val = param_def.max_value
            if min_val is not None and max_val is not None:
                if not (min_val <= Decimal(str(value)) <= max_val):
                    return 'OUT_OF_SPEC'
        return 'IN_SPEC'



class AssignAnalystSerializer(serializers.Serializer):
    """
    A simple serializer to validate the analyst being assigned to a TestRecord.
    """
    analyst_id = serializers.IntegerField()

    def validate_analyst_id(self, value):
        # Check if the user exists and is an analyst
        try:
            user = User.objects.get(pk=value)
            if not user.groups.filter(name='Analyst').exists():
                raise serializers.ValidationError("This user is not a Analyst.")
        except User.DoesNotExist:
            raise serializers.ValidationError("An analyst with this ID does not exist.")
        return value


class TestRecordSerializer(serializers.ModelSerializer):
    parameter_values = TestResultDisplaySerializer(many=True, read_only=True)
    results_input = TestResultInputSerializer(many=True, write_only=True, source='parameter_values')
    analyst_username = serializers.CharField(source='analyst.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_grade_name = serializers.CharField(source='product_grade.name', read_only=True, allow_null=True)
    record_id = serializers.CharField(read_only=True)
    retest_record_id = serializers.CharField(source='retest_of.record_id', read_only=True)
    retests = serializers.SerializerMethodField()
    class Meta:
        model = TestRecord
        fields = [
            'id', 'record_id', 'retest_record_id', 'retests',
            'product', 'product_grade', 'sample_id', 'batch_no', 'test_date', 'status',
            'analyst', 'analyst_username',
            'supervisor_comments', 'approved_by', 'approved_at',
            'created_at', 'updated_at',
            'product_name', 'product_grade_name',
            'parameter_values',  'results_input',
        ]
        read_only_fields = ('analyst', 'approved_by', 'approved_at', 'test_date', 'retest_of')

    @transaction.atomic
    def create(self, validated_data):
        parameter_values_data = validated_data.pop('parameter_values')
        validated_data['analyst'] = self.context['request'].user
        test_record = TestRecord.objects.create(**validated_data)
        for result_data in parameter_values_data:
            TestResult.objects.create(test_record=test_record, **result_data)
        return test_record

    @transaction.atomic
    def update(self, instance, validated_data):
        parameter_values_data = validated_data.pop('parameter_values', None)
        instance = super().update(instance, validated_data)
        if parameter_values_data is not None:
            existing_results = {result.parameter.id: result for result in instance.parameter_values.all()}
            for result_data in parameter_values_data:
                parameter = result_data['parameter']
                if parameter.id in existing_results:
                    result_instance = existing_results.pop(parameter.id)
                    result_instance.value_decimal = result_data.get('value_decimal')
                    result_instance.value_string = result_data.get('value_string')
                    result_instance.value_boolean = result_data.get('value_boolean')
                    result_instance.save()
                else:
                    TestResult.objects.create(test_record=instance, **result_data)
            if existing_results:
                TestResult.objects.filter(id__in=[res.id for res in existing_results.values()]).delete()

        if instance.status == 'PENDING_RETEST':
            instance.status = 'PENDING'
            instance.save(update_fields=['status'])
            
            # Log this important status change
            log_custom_event(
                instance=instance,
                action_type='RESULTS_SUBMITTED',
                user=self.context['request'].user,
                details=f"Analyst submitted results for a retest. Status updated to PENDING."
            )

        return instance

    def get_retests(self, obj):
        # This will return a list of primary keys, e.g., [8, 9]
        return [r.id for r in obj.retests.all()]

class TestRecordForAlertContextSerializer(serializers.ModelSerializer):
    results = TestResultDisplaySerializer(many=True, read_only=True, source='parameter_values')
    class Meta:
        model = TestRecord
        fields = ['id', 'sample_id', 'created_at', 'status', 'results']