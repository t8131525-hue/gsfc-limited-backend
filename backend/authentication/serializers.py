# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model # Use get_user_model for flexibility

User = get_user_model() # This will now correctly point to your custom user model

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)

class UserDetailSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        # Add the 'role' field to the list of fields
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined', 'last_login', 'groups')
        read_only_fields = ('id', 'username', 'is_staff', 'is_active', 'date_joined', 'last_login', 'groups')