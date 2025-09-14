# audit_trail/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
import json
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'action_type', 'linked_object', 'ip_address')
    list_filter = ('action_type', 'user', 'content_type')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    
    readonly_fields = ('action_time', 'user', 'action_type', 'linked_object', 
                       'object_repr', 'formatted_change_details', 'ip_address')

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    # --- START: MODIFIED linked_object METHOD ---
    def linked_object(self, obj):
        """
        A defensive method to create a clickable link to the audited object.
        It now handles three cases:
        1. The object exists.
        2. The object has been deleted.
        3. The log is not linked to any object (e.g., a LOGIN event).
        """
        # First, check if the log entry is meant to be linked to an object.
        if obj.content_type and obj.object_id:
            # Generate the admin URL.
            admin_url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            # Check if the linked object still exists.
            if obj.content_object:
                return format_html('<a href="{}">{}</a>', admin_url, obj.object_repr)
            else:
                # If the object was deleted, show its last known representation.
                return f"{obj.object_repr} [Deleted]"
        # If there's no content_type, it's likely a system-level action.
        return "N/A"
    linked_object.short_description = 'Audited Object'
    # --- END: MODIFIED linked_object METHOD ---

    def formatted_change_details(self, obj):
        if obj.change_details:
            pretty_json = json.dumps(obj.change_details, indent=4)
            return format_html('<pre>{}</pre>', pretty_json)
        return "No changes recorded."
    formatted_change_details.short_description = 'Changes'