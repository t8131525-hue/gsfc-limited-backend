# inventory/filters.py
import django_filters
from .models import TestRecord


class TestRecordFilter(django_filters.FilterSet):
    """
    Custom filter set for TestRecord to enable advanced filtering.
    """

    date_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    analyst__isnull = django_filters.BooleanFilter(
        field_name="analyst", lookup_expr="isnull"
    )
    retest_of__isnull = django_filters.BooleanFilter(
        field_name="retest_of", lookup_expr="isnull"
    )

    class Meta:
        model = TestRecord
        fields = [
            "status",
            "analyst",
            "date_after",
            "date_before",
            "analyst__isnull",
            "retest_of__isnull",
            "lab",
        ]
