from django.urls import path
from rest_framework.routers import DefaultRouter

# This single, clean import now works because your __init__.py is set up correctly.
from inventory.views import (
    ProductViewSet,
    ProductGradeViewSet,
    ParameterDefinitionViewSet,
    TestRecordViewSet,
    SpecificationViewSet,
    InventoryStatsView,
)

router = DefaultRouter()

# These registrations should now work without the AssertionError
router.register(r'products', ProductViewSet, basename='product')
router.register(r'grades', ProductGradeViewSet, basename='productgrade')
router.register(r'parameters', ParameterDefinitionViewSet, basename='parameterdefinition')
router.register(r'specifications', SpecificationViewSet, basename='specification') 
router.register(r'tests', TestRecordViewSet, basename='testrecord')

urlpatterns = router.urls

urlpatterns += [
    path('stats/', InventoryStatsView.as_view(), name='inventory-stats'),
]
