from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Min, Max
from django.db.models.functions import TruncDate

from ..models import Product, TestResult, TestRecord
from ..serializers import ProductQualityDetailSerializer


class ProductQualityDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id, *args, **kwargs):
        product = get_object_or_404(Product, pk=product_id)
        active_version = product.versions.filter(is_active=True).first()

        if not active_version:
            return Response(
                {"error": "This product does not have an active version."},
                status=status.HTTP_404_NOT_FOUND,
            )
        end_date_str = request.query_params.get(
            "end_date", timezone.now().strftime("%Y-%m-%d")
        )
        start_date_str = request.query_params.get(
            "start_date", (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        )
        trends_data = []
        grades_data = []
        has_grades = active_version.grades.exists()

        if has_grades:
            for grade in active_version.grades.all():
                grade_trends = []
                for param in grade.parameters.all():
                    daily_aggregates = (
                        TestResult.objects.filter(
                            parameter=param,
                            test_record__version=active_version,
                            test_record__product_grade=grade,
                            test_record__created_at__date__range=[
                                start_date_str,
                                end_date_str,
                            ],
                            test_record__status__in=["APPROVED", "CLOSED"],
                        )
                        .annotate(date=TruncDate("test_record__created_at"))
                        .order_by("date")
                        .values("date")
                        .annotate(
                            avg=Avg("value_decimal"),
                            min=Min("value_decimal"),
                            max=Max("value_decimal"),
                        )
                    )
                    param.data_points = list(daily_aggregates)
                    grade_trends.append(param)
                grade.trends = grade_trends
                grades_data.append(grade)
        else:
            for param in active_version.parameters.all():
                daily_aggregates = (
                    TestResult.objects.filter(
                        parameter=param,
                        test_record__version=active_version,
                        test_record__created_at__date__range=[
                            start_date_str,
                            end_date_str,
                        ],
                        test_record__status__in=["APPROVED", "CLOSED"],
                    )
                    .annotate(date=TruncDate("test_record__created_at"))
                    .order_by("date")
                    .values("date")
                    .annotate(
                        avg=Avg("value_decimal"),
                        min=Min("value_decimal"),
                        max=Max("value_decimal"),
                    )
                )
                param.data_points = list(daily_aggregates)
                trends_data.append(param)

        recent_tests = TestRecord.objects.filter(version__product=product).order_by(
            "-created_at"
        )[:10]

        context_data = {
            "id": product.id,
            "name": product.name,
            "product_id": product.product_id,
            "active_version": active_version,
            "has_grades": has_grades,
            "grades": grades_data,
            "trends": trends_data,
            "recent_tests": recent_tests,
        }

        serializer = ProductQualityDetailSerializer(context_data)
        return Response(serializer.data)
