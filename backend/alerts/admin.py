# alerts/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'linked_test_record', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',) 
    readonly_fields = ('test_result', 'linked_test_record', 'details', 'created_at', 'updated_at')
    search_fields = ['test_record__sample_id', 'test_record__product__name'] # Makes searching easier

    def linked_test_record(self, obj):
        # Creates a clickable link to the TestRecord admin page
        url = reverse("admin:inventory_testrecord_change", args=[obj.test_record.id])
        return format_html('<a href="{}">{}</a>', url, obj.test_record)
    
    linked_test_record.short_description = "Test Record (Click to View)"