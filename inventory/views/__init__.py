# inventory/views/__init__.py

from .InventoryStatsView import InventoryStatsView
from .ParameterDefinitionViewSet import ParameterDefinitionViewSet
from .VersionViewSet import VersionViewSet
from .ProductGradeViewSet import ProductGradeViewSet
from .ProductViewSet import ProductViewSet
from .TestRecordViewSet import TestRecordViewSet
from .TestResultViewSet import TestResultViewSet
from .LabViewSet import LabViewSet
from .DailyStatsView import DailyStatsView
from .UserStatsView import UserSummaryCountsView, UserPerformanceChartView
from .ProductDetailView import ProductQualityDetailView
__all__ = [
    "InventoryStatsView",
    "ParameterDefinitionViewSet",
    "ProductGradeViewSet",
    "ProductViewSet",
    "TestRecordViewSet",
    "TestResultViewSet",
    "VersionViewSet",
    "LabViewSet",
    "DailyStatsView",
    "UserSummaryCountsView",
    "UserPerformanceChartView",
    # "QualityTrendView",
    "ProductQualityDetailView",
]
