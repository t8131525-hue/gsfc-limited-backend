# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("id", "name", "codename")


class UserDetailSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    all_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Update the fields list to use our new 'all_permissions' field
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "date_joined",
            "last_login",
            "groups",
            "all_permissions",  # Use the new field
        )
        read_only_fields = (
            "id",
            "username",
            "is_staff",
            "is_active",
            "date_joined",
            "last_login",
            "groups",
            "all_permissions",
        )

    def get_all_permissions(self, obj):
        """
        Gathers all permission codenames for the user, including those 
        from groups, and returns them as a simple list of strings.
        """
        return sorted(list(obj.get_all_permissions()))



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserDetailSerializer(self.user)
        data["user"] = serializer.data
        return data
