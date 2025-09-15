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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer to add user data to the login response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # You could add custom claims to the token here if needed
        return token

    def validate(self, attrs):
        # The default validate method returns the access and refresh tokens.
        data = super().validate(attrs)
        
        # Serialize the user data and add it to the response.
        serializer = UserDetailSerializer(self.user)
        data['user'] = serializer.data
        
        return data