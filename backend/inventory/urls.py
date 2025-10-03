from django.urls import path
from rest_framework.routers import DefaultRouter

# Import all your corrected ViewSets
from inventory.views import (
    ProductViewSet,
    ProductGradeViewSet,
    ParameterDefinitionViewSet,
    TestRecordViewSet,
    VersionViewSet, # <-- Corrected: Renamed from SpecificationViewSet
    TestResultViewSet,
    InventoryStatsView,
    LabViewSet, 
     DailyStatsView,
)

router = DefaultRouter()

# Register the ViewSets with the router
router.register(r'labs', LabViewSet, basename='lab') 
router.register(r'products', ProductViewSet, basename='product')
router.register(r'grades', ProductGradeViewSet, basename='productgrade')
router.register(r'parameters', ParameterDefinitionViewSet, basename='parameterdefinition')
router.register(r'versions', VersionViewSet, basename='version') # <-- Corrected: Renamed from 'specifications'
router.register(r'tests', TestRecordViewSet, basename='testrecord')
router.register(r'results', TestResultViewSet, basename='testresult')


urlpatterns = router.urls

# Add the custom stats endpoint
urlpatterns += [
    path("stats/daily-records/", DailyStatsView.as_view(), name="daily_record_stats"),
    path('stats/', InventoryStatsView.as_view(), name='inventory-stats'),
]