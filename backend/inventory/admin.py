from django.contrib import admin
from .models import Lab

@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    """
    Admin interface options for the Lab model.
    """
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    
    # This is the key for a great user experience with ManyToManyFields.
    # It provides a dual-listbox interface for selecting users and groups.
    filter_horizontal = ('accessible_by_groups', 'accessible_by_users')

    # Organize the fields in the detail view for better clarity.
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Access Control', {
            'classes': ('collapse',),
            'fields': ('accessible_by_groups', 'accessible_by_users'),
            'description': 'Control which user groups or specific users can access this lab.'
        }),
    )
