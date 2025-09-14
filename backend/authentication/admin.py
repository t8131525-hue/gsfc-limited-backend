# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User  # Import your custom user model


class CustomUserAdmin(UserAdmin):
    model = User
    # Remove 'role' from the list_display as it no longer exists on the model.
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )

    # The base UserAdmin already includes fields for managing 'groups' and 'user_permissions'.
    # We remove the old fieldset that included 'role'.
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets


admin.site.register(User, CustomUserAdmin)
