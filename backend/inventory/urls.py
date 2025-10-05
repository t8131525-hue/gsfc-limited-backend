from django.urls import path
from rest_framework.routers import DefaultRouter

# Import all your corrected ViewSets
from inventory.views import (
    ProductViewSet,
    ProductGradeViewSet,
    ParameterDefinitionViewSet,
    TestRecordViewSet,
    VersionViewSet,
    TestResultViewSet,
    InventoryStatsView,
    LabViewSet,
    DailyStatsView,
    UserPerformanceChartView, 
    UserSummaryCountsView,
)

router = DefaultRouter()

# Register the ViewSets with the router
router.register(r"labs", LabViewSet, basename="lab")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"grades", ProductGradeViewSet, basename="productgrade")
router.register(
    r"parameters", ParameterDefinitionViewSet, basename="parameterdefinition"
)
router.register(r"versions", VersionViewSet, basename="version")
router.register(r"tests", TestRecordViewSet, basename="testrecord")
router.register(r"results", TestResultViewSet, basename="testresult")


urlpatterns = router.urls

urlpatterns += [
    path("stats/daily-records/", DailyStatsView.as_view(), name="daily_record_stats"),
    path("stats/", InventoryStatsView.as_view(), name="inventory-stats"),
     path(
        "stats/users/<int:user_id>/performance-chart/",
        UserPerformanceChartView.as_view(),
        name="user_performance_chart",
    ),
    
    # ✅ FIX: Change 'user' to 'users' here as well
    path(
        "stats/users/<int:user_id>/summary-counts/",
        UserSummaryCountsView.as_view(),
        name="user_summary_counts",
    ),
]
