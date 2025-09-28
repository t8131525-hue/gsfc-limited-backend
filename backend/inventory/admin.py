# # inventory/admin.py
# from django.contrib import admin
# from inventory.models import (
#     Lab,
#     Product,
#     ParameterDefinition,
#     Version,
#     TestRecord,
#     TestResult,
# )


# # This inline allows viewing/editing Specifications directly from the Product page.
# class SpecificationInline(admin.TabularInline):
#     model = Version
#     extra = 0  # Don't show empty forms for new versions by default
#     fields = ("name", "version", "is_active")
#     readonly_fields = ("name", "version", "is_active")
#     show_change_link = True  # Allows clicking to the full Specification admin page


# # This inline allows editing TestResults directly from the TestRecord page.
# class TestResultInline(admin.TabularInline):
#     model = TestResult
#     extra = 1
#     fields = ("parameter", "value_decimal", "value_string", "value_boolean")
#     # Make the parameter field a dropdown that's easier to search
#     autocomplete_fields = ["parameter"]


# @admin.register(Lab)
# class LabAdmin(admin.ModelAdmin):
#     list_display = ("name", "description")
#     search_fields = ("name",)
#     # Use a better UI for ManyToMany fields
#     filter_horizontal = ("accessible_by_groups", "accessible_by_users")


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ("name", "product_id", "description")
#     search_fields = ("name", "product_id")
#     readonly_fields = ("product_id",)
#     # Show related specifications directly on the product page
#     inlines = [SpecificationInline]


# @admin.register(ParameterDefinition)
# class ParameterDefinitionAdmin(admin.ModelAdmin):
#     # This is now a simple library of parameters
#     list_display = ("name", "data_type", "unit", "description")
#     list_filter = ("data_type",)
#     search_fields = ("name", "unit")


# @admin.register(Version)
# class SpecificationAdmin(admin.ModelAdmin):
#     list_display = ("__str__", "version", "is_active", "product")
#     list_filter = ("is_active", "product")
#     search_fields = ("name", "product__name", "version")
#     readonly_fields = ("activated_at", "created_at")
#     # Use a better UI for selecting parameters
#     filter_horizontal = ("parameters",)
#     list_display_links = ("__str__", "version")


# @admin.register(TestRecord)
# class TestRecordAdmin(admin.ModelAdmin):
#     list_display = (
#         "record_id",
#         "specification",
#         "lab",
#         "status",
#         "analyst",
#         "created_at",
#     )
#     list_filter = ("status", "lab", "analyst", "specification__product")
#     search_fields = ("record_id", "sample_id", "batch_no", "specification__name")
#     readonly_fields = ("created_at", "updated_at", "approved_at", "record_id")
#     # Allow quick data entry for test results from the record page
#     inlines = [TestResultInline]
#     # Make the specification field a searchable dropdown
#     autocomplete_fields = ["specification", "lab", "analyst", "approved_by"]


# @admin.register(TestResult)
# class TestResultAdmin(admin.ModelAdmin):
#     # This view is useful for searching all results globally
#     list_display = (
#         "id",
#         "test_record",
#         "parameter",
#         "value_decimal",
#         "value_string",
#         "value_boolean",
#     )
#     list_filter = ("parameter",)
#     autocomplete_fields = ["test_record", "parameter"]
