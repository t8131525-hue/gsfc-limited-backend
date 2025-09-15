from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AssignAnalystSerializer(serializers.Serializer):
    """
    A simple serializer to validate the analyst being assigned to a TestRecord.
    """

    analyst_id = serializers.IntegerField()

    def validate_analyst_id(self, value):
        # Check if the user exists and is an analyst
        try:
            user = User.objects.get(pk=value)
            if not user.groups.filter(name="Analyst").exists():
                raise serializers.ValidationError("This user is not a Analyst.")
        except User.DoesNotExist:
            raise serializers.ValidationError("An analyst with this ID does not exist.")
        return value
