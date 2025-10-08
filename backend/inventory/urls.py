from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
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
    QualityTrendView,
    ProductHealthDashboardView,
)

router = DefaultRouter()
router.register(r"labs", LabViewSet, basename="lab")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"grades", ProductGradeViewSet, basename="productgrade")
router.register(
    r"parameters", ParameterDefinitionViewSet, basename="parameterdefinition"
)
router.register(r"versions", VersionViewSet, basename="version")
router.register(r"tests", TestRecordViewSet, basename="testrecord")
router.register(r"results", TestResultViewSet, basename="testresult")

urlpatterns = router.urls + [
    path("stats/daily-records/", DailyStatsView.as_view(), name="daily_record_stats"),
    path("stats/", InventoryStatsView.as_view(), name="inventory-stats"),
    path(
        "stats/users/<int:user_id>/performance-chart/",
        UserPerformanceChartView.as_view(),
        name="user_performance_chart",
    ),
    path("stats/quality-trends/", QualityTrendView.as_view(), name="quality-trends"),
    path(
        "stats/users/<int:user_id>/summary-counts/",
        UserSummaryCountsView.as_view(),
        name="user_summary_counts",
    ),
    path(
        "dashboard/product-health/",
        ProductHealthDashboardView.as_view(),
        name="dashboard-product-health",
    ),
]
