from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Min, Max
from django.db.models.functions import TruncDate

from ..models import Product, TestResult, TestRecord, ParameterDefinition
from ..serializers import ProductQualityDetailSerializer


class ProductQualityDetailView(APIView):
    """
    Provides all necessary data for a single product's quality trend detail page.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id, *args, **kwargs):
        product = get_object_or_404(Product, pk=product_id)
        active_version = product.versions.filter(is_active=True).first()

        if not active_version:
            return Response(
                {"error": "This product does not have an active version."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 1. Get Date Range for Chart
        end_date_str = request.query_params.get(
            "end_date", timezone.now().strftime("%Y-%m-%d")
        )
        start_date_str = request.query_params.get(
            "start_date", (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        )

        # 2. Get Parameters for the Active Version
        if active_version.grades.exists():
            parameters = ParameterDefinition.objects.filter(
                content_type__model="productgrade",
                object_id__in=active_version.grades.values_list("id", flat=True),
            )
        else:
            parameters = active_version.parameters.all()

        # 3. Get Aggregated Trend Data for each parameter
        trends_data = []
        for param in parameters:
            daily_aggregates = (
                TestResult.objects.filter(
                    parameter=param,
                    test_record__version=active_version,
                    test_record__created_at__date__range=[start_date_str, end_date_str],
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

            param.data_points = list(daily_aggregates)
            trends_data.append(param)

        # 4. Get Recent Test Records
        recent_tests = TestRecord.objects.filter(version__product=product).order_by(
            "-created_at"
        )[:10]

        # 5. Assemble the final data object
        context_data = {
            "id": product.id,
            "name": product.name,
            "product_id": product.product_id,
            "active_version": active_version,
            "trends": trends_data,
            "recent_tests": recent_tests,
        }

        serializer = ProductQualityDetailSerializer(context_data)
        return Response(serializer.data)
