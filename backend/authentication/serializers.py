# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model

User = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name",)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        # Serialize the name and codename for clarity on the frontend
        fields = ("id", "name", "codename")


class UserDetailSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    # It's useful to see a user's specific, directly assigned permissions
    user_permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = User
        # Remove 'role' and add 'user_permissions' to the fields tuple
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
            "user_permissions",
        )
        read_only_fields = (
            "id",
            "username",
            "is_staff",
            "is_active",
            "date_joined",
            "last_login",
            "groups",
            "user_permissions",
        )
