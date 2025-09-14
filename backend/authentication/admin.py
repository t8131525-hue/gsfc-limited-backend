# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User # Import your custom user model

# Add the 'role' field to the admin display and forms
class CustomUserAdmin(UserAdmin):
    model = User
    # Add 'role' to the list display
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    # Add 'role' to the fieldsets to make it editable in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)