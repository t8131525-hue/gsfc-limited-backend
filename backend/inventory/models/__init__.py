# inventory/models/__init__.py

from .Lab import Lab
from .ParameterDefinition import ParameterDefinition
from .Product import Product
from .ProductGrade import ProductGrade
from .Specification import Specification
from .TestRecord import TestRecord
from .TestResult import TestResult

__all__ = [
    'Lab',
    'ParameterDefinition',
    'Product',
    'ProductGrade',
    'Specification',
    'TestRecord',
    'TestResult',
]
