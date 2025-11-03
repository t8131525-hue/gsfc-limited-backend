from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import (
    Lab,
    Product,
    Version,
    ProductGrade,
    ParameterDefinition,
    TestRecord,
    TestResult,
)

# =============================================================================
# INLINE DEFINITIONS
# Inlines allow editing related models on the same page as the parent model.
# =============================================================================

class ParameterDefinitionInline(GenericTabularInline):
    """
    A generic inline for ParameterDefinitions.
    This can be attached to any model that has a GenericRelation to it,
    like Version or ProductGrade.
    """
    model = ParameterDefinition
    extra = 1  # Show one empty form for adding a new parameter
    fields = (
        "name",
        "data_type",
        "unit",
        "min_value",
        "max_value",
        "is_required",
    )
    ordering = ("name",)


class ProductGradeInline(admin.TabularInline):
    """
    Allows managing ProductGrades directly from the Version admin page.
    """
    model = ProductGrade
    extra = 1
    fields = ("name", "description")
    show_change_link = True


class VersionInline(admin.TabularInline):
    """
    Allows managing Versions directly from the Product admin page.
    """
    model = Version
    extra = 0  # Don't show empty forms by default, versions are significant
    fields = ("version_name", "status", "is_active")
    readonly_fields = ("status", "is_active")
    show_change_link = True


class TestResultInline(admin.TabularInline):
    """
    Allows managing TestResults (the actual values) from the TestRecord page.
    """
    model = TestResult
    extra = 0  # Parameters are pre-defined, so don't show empty forms
    fields = (
        "parameter",
        "value_string",
        "value_decimal",
        "value_boolean",
    )
    # Autocomplete for selecting from a potentially long list of parameters
    autocomplete_fields = ("parameter",)
    
    def get_queryset(self, request):
        """
        Optimize the queryset to prefetch the related parameter definition.
        """
        return super().get_queryset(request).select_related('parameter')


# =============================================================================
# MODEL ADMIN DEFINITIONS
# These classes define the admin interface for each model.
# =============================================================================

@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    """
    Admin interface for Lab model.
    """
    list_display = ("name", "description")
    search_fields = ("name",)
    filter_horizontal = ("accessible_by_groups", "accessible_by_users")
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            "Access Control",
            {
                "classes": ("collapse",),
                "fields": ("accessible_by_groups", "accessible_by_users"),
            },
        ),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.
    Includes an inline for managing related Versions.
    """
    list_display = ("name", "product_id", "created_at")
    search_fields = ("name", "product_id")
    readonly_fields = ("product_id", "created_at", "updated_at")
    inlines = [VersionInline]


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    """
    Admin interface for Version model.
    Allows for inline management of ProductGrades and direct ParameterDefinitions.
    """
    list_display = ("__str__", "product", "version_name", "status", "is_active")
    list_filter = ("status", "is_active", "product")
    search_fields = ("product__name", "version_name")
    readonly_fields = ("locked_at", "created_at", "activated_at")
    autocomplete_fields = ("product",)
    inlines = [ProductGradeInline, ParameterDefinitionInline]
    fieldsets = (
        (None, {"fields": ("product", "version_name", "description")}),
        (
            "Status & Activation",
            {
                "fields": ("status", "is_active", "locked_at", "activated_at"),
                "description": "Activate a version to make it the current standard for testing. Must be LOCKED first.",
            },
        ),
    )


@admin.register(ProductGrade)
class ProductGradeAdmin(admin.ModelAdmin):
    """
    Admin interface for ProductGrade model.
    Includes an inline for managing its specific parameters.
    """
    list_display = ("name", "version", "created_at")
    search_fields = ("name", "version__product__name", "version__version_name")
    autocomplete_fields = ("version",)
    inlines = [ParameterDefinitionInline]


@admin.register(ParameterDefinition)
class ParameterDefinitionAdmin(admin.ModelAdmin):
    """
    A read-only view of all ParameterDefinitions in the system.
    Management should be done via inlines on Version or ProductGrade pages.
    """
    list_display = ("name", "data_type", "unit", "owner")
    list_filter = ("data_type",)
    search_fields = ("name", "description")
    readonly_fields = ["content_type", "object_id", "owner"]


@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for TestRecord model.
    This is the central point for lab technicians to view and manage tests.
    """
    list_display = (
        "record_id",
        "version",
        "status",
        "analyst",
        "approved_by",
        "created_at",
    )
    list_filter = ("status", "lab", "created_at")
    search_fields = ("record_id", "batch_no", "sample_id", "version__product__name")
    readonly_fields = ("record_id", "created_at", "updated_at", "approved_at")
    autocomplete_fields = (
        "version",
        "lab",
        "product_grade",
        "analyst",
        "approved_by",
        "retest_of",
    )
    inlines = [TestResultInline]
    fieldsets = (
        (
            "Sample Information",
            {
                "fields": (
                    "record_id",
                    "version",
                    "lab",
                    "product_grade",
                    "batch_no",
                    "sample_id",
                )
            },
        ),
        (
            "Workflow & Status",
            {
                "fields": (
                    "status",
                    "analyst",
                    "supervisor_comments",
                    "approved_by",
                    "approved_at",
                )
            },
        ),
        ("Retest Information", {"classes": ("collapse",), "fields": ("retest_of",)}),
    )


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    """
    Admin interface for TestResult model.
    Primarily for viewing all results in one place or for debugging.
    Editing should be done via the TestRecord page.
    """
    list_display = ("test_record", "parameter", "get_value", "updated_at")
    search_fields = ("test_record__record_id", "parameter__name")
    autocomplete_fields = ("test_record", "parameter")
    readonly_fields = ("created_at", "updated_at")

    def get_value(self, obj):
        """
        Display the actual recorded value in the list view,
        regardless of which field it's stored in.
        """
        if obj.parameter.data_type in ["INTEGER", "DECIMAL"]:
            return obj.value_decimal
        elif obj.parameter.data_type in ["STRING", "ENUM"]:
            return obj.value_string
        elif obj.parameter.data_type == "BOOLEAN":
            return obj.value_boolean
        return "N/A"

    get_value.short_description = "Recorded Value"
