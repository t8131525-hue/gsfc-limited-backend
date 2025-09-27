# inventory/views/__init__.py

from .InventoryStatsView import InventoryStatsView
from .ParameterDefinitionViewSet import ParameterDefinitionViewSet
from .SpecificationViewSet import SpecificationViewSet
from .ProductGradeViewSet import ProductGradeViewSet
from .ProductViewSet import ProductViewSet
from .TestRecordViewSet import TestRecordViewSet
from .TestResultViewSet import TestResultViewSet

__all__ = [
    'InventoryStatsView',
    'ParameterDefinitionViewSet',
    'ProductGradeViewSet',
    'ProductViewSet',
    'TestRecordViewSet',
    'TestResultViewSet',
    'SpecificationViewSet'
]

