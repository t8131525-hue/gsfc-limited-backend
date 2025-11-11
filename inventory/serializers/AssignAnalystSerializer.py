from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AssignAnalystSerializer(serializers.Serializer):
    """
    A simple serializer to validate the analyst being assigned to a TestRecord.
    """

    analyst_id = serializers.IntegerField()

    def validate_analyst_id(self, value):
        # Check if the user exists
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("A user with this ID does not exist.")
        if not user.has_perm("inventory.can_manage_test_records"):
            raise serializers.ValidationError(
                "This user does not have permission to manage test records."
            )

        return value
