from django.urls import path # Make sure path is imported
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductGradeViewSet, ParameterDefinitionViewSet, TestRecordViewSet, InventoryStatsView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'grades', ProductGradeViewSet)
router.register(r'parameters', ParameterDefinitionViewSet)
router.register(r'tests', TestRecordViewSet, basename='testrecord') # <--- Add basename here

urlpatterns = router.urls

# --- ADD THIS NEW URL PATTERN AT THE END ---
urlpatterns += [
    path('stats/', InventoryStatsView.as_view(), name='inventory-stats'),
]
