# inventory/views/UserStatsView.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, DateField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear, Cast

from ..models import TestRecord
from ..serializers import UserPerformanceSerializer, UserSummaryCountsSerializer

User = get_user_model()

class UserPerformanceChartView(APIView):
    """
    Provides time-series data of test records created by a specific user.
    Accepts query parameters:
    - group_by: 'day', 'week', 'month', 'year' (default: 'week')
    - date_after: YYYY-MM-DD
    - date_before: YYYY-MM-DD
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        queryset = TestRecord.objects.filter(analyst=user)

        # Handle date range filtering
        date_after = request.query_params.get('date_after')
        date_before = request.query_params.get('date_before')
        if date_after:
            queryset = queryset.filter(created_at__date__gte=date_after)
        if date_before:
            queryset = queryset.filter(created_at__date__lte=date_before)

        # Handle time-based grouping
        group_by = request.query_params.get('group_by', 'week')
        trunc_field = {
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
            'year': TruncYear
        }.get(group_by, TruncWeek)

        chart_data = (
            queryset.annotate(
                truncated_date=trunc_field('created_at')
            )
            .annotate(
                date=Cast('truncated_date', output_field=DateField())
            )
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        serializer = UserPerformanceSerializer(chart_data, many=True)
        return Response(serializer.data)


class UserSummaryCountsView(APIView):
    """
    Provides summary counts of test records for a specific user over
    various time periods (today, this week, this month, etc.).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        today = now.date()
        
        base_queryset = TestRecord.objects.filter(analyst=user)

        # Calculate counts for different periods
        stats = {
            'count_today': base_queryset.filter(created_at__date=today).count(),
            'count_week': base_queryset.filter(created_at__gte=today - timedelta(days=7)).count(),
            'count_month': base_queryset.filter(created_at__gte=today - timedelta(days=30)).count(),
            'count_3_months': base_queryset.filter(created_at__gte=today - timedelta(days=90)).count(),
            'count_6_months': base_queryset.filter(created_at__gte=today - timedelta(days=180)).count(),
            'count_year': base_queryset.filter(created_at__gte=today - timedelta(days=365)).count(),
        }

        serializer = UserSummaryCountsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)