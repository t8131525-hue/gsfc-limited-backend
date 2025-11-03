# alerts/filters.py
import django_filters
from .models import Alert


class AlertFilter(django_filters.FilterSet):
    """
    Custom filter set for Alerts to enable date range filtering.
    """

    date_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Alert
        fields = ["status", "test_record", "date_after", "date_before"]
