# inventory/admin.py
from django.contrib import admin
from inventory.models.Product import Product
from inventory.models.ProductGrade import ProductGrade
from inventory.models.ParameterDefinition import ParameterDefinition
from inventory.models.TestRecord import TestRecord
from inventory.models.TestResult import TestResult  # <- fixes the error


# --- ADD THIS INLINE CONFIGURATION AT THE TOP ---
class TestResultInline(admin.TabularInline):
    """
    This configuration allows editing TestResults directly within the
    TestRecord admin page, making data entry much faster.
    """
    model = TestResult
    extra = 1  # Shows one empty row by default for adding new results
    # You can add more fields here if you want them to be editable in the table
    fields = ('parameter', 'value_decimal', 'value_string', 'value_boolean')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ProductGrade)
class ProductGradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'product')
    list_filter = ('product',)

@admin.register(ParameterDefinition)
class ParameterDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'data_type', 'product', 'product_grade')
    list_filter = ('product', 'product_grade')
    fieldsets = (
        (None, {'fields': ('name', 'data_type', 'unit', 'is_required')}),
        ('Normal Range (for numeric types)', {'fields': ('min_value', 'max_value')}),
        ('Scope (Choose One)', {'fields': ('product', 'product_grade')}),
        ('Enum Options', {'classes': ('collapse',), 'fields': ('enum_options',)}),
    )

@admin.register(TestRecord)
class TestRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_id', 'product', 'product_grade', 'test_date', 'status')
    list_filter = ('status', 'product')
    # --- ADD THIS LINE TO ACTIVATE THE INLINE TABLE ---
    inlines = [TestResultInline]

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    # This separate admin for TestResult is still useful for searching and filtering all results globally.
    list_display = ('id', 'test_record', 'parameter', 'value_decimal', 'value_string', 'value_boolean')
    list_filter = ('parameter',)