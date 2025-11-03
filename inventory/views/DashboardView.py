# inventory/views/DashboardView.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Min, Max  # ✅ 1. Import aggregation functions
from django.db.models.functions import TruncDate
from ..models import Product, TestResult, TestRecord, ParameterDefinition


class ProductHealthDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        include_outliers = (
            request.query_params.get("include_outliers", "true").lower() != "false"
        )

        dashboard_data = []
        products_with_active_version = Product.objects.filter(
            versions__is_active=True
        ).distinct()
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)

        for product in products_with_active_version:
            active_version = product.versions.filter(is_active=True).first()
            if not active_version:
                continue

            # ... (Parameter fetching logic is unchanged)
            if active_version.grades.exists():
                parameters = ParameterDefinition.objects.filter(
                    content_type__model="productgrade",
                    object_id__in=active_version.grades.values_list("id", flat=True),
                )[:4]
            else:
                parameters = active_version.parameters.all()[:4]

            product_info = {
                "product_id": product.id,
                "product_name": product.name,
                "active_version_id": active_version.id,
                "active_version_name": active_version.version_name,
                "trends": [],
            }
            last_record = (
                TestRecord.objects.filter(version=active_version, status="CLOSED")
                .order_by("-closed_at")
                .first()
            )
            product_info["last_updated_at"] = (
                last_record.closed_at if last_record else None
            )

            for param in parameters:
                results_queryset = TestResult.objects.filter(
                    parameter=param,
                    test_record__version=active_version,
                    test_record__created_at__date__range=[start_date, end_date],
                    test_record__status__in=["APPROVED", "CLOSED"],
                )
                if not include_outliers:
                    results_queryset = results_queryset.filter(alert__isnull=True)
                daily_aggregates = (
                    TestResult.objects.filter(
                        parameter=param,
                        test_record__version=active_version,
                        test_record__created_at__date__range=[start_date, end_date],
                        test_record__status__in=["APPROVED", "CLOSED"],
                    )
                    .annotate(date=TruncDate("test_record__created_at"))
                    .values("date")
                    .annotate(
                        avg=Avg("value_decimal"),
                        min=Min("value_decimal"),
                        max=Max("value_decimal"),
                    )
                    .order_by("date")
                )
                trend_data = {
                    "id": param.id,
                    "name": param.name,
                    "unit": param.unit,
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "data_points": list(daily_aggregates),
                }
                product_info["trends"].append(trend_data)

            dashboard_data.append(product_info)

        return Response(dashboard_data)
