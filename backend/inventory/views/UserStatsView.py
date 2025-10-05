# inventory/views/UserStatsView.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, DateField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear, Cast

from ..models import TestRecord
from ..serializers import UserPerformanceSerializer, UserSummaryCountsSerializer

User = get_user_model()


class UserPerformanceChartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # ✅ 1. SIMPLIFIED DATE LOGIC: Use frontend dates if available, otherwise default to 7 days.
        try:
            date_after_str = request.query_params.get("date_after")
            date_before_str = request.query_params.get("date_before")

            end_date = (
                date.fromisoformat(date_before_str)
                if date_before_str
                else timezone.now().date()
            )
            start_date = (
                date.fromisoformat(date_after_str)
                if date_after_str
                else end_date - timedelta(days=6)
            )
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # We will now always group by day and let the frontend decide the range.
        # The zero-filling logic is perfect for this.
        duration = end_date - start_date
        all_dates = {
            (start_date + timedelta(days=i)).isoformat(): 0
            for i in range(duration.days + 1)
        }

        db_counts = (
            TestRecord.objects.filter(
                analyst=user,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .annotate(date=Cast(TruncDay("created_at"), output_field=DateField()))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        for item in db_counts:
            date_str = item["date"].isoformat()
            if date_str in all_dates:
                all_dates[date_str] = item["count"]

        chart_data = [
            {"date": date_str, "count": count} for date_str, count in all_dates.items()
        ]

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
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # ✅ FIX: Use 'now' (an aware datetime) for all calculations, not 'today'
        now = timezone.now()

        base_queryset = TestRecord.objects.filter(analyst=user)

        # Calculate counts using aware datetimes to prevent warnings
        stats = {
            "count_today": base_queryset.filter(created_at__date=now.date()).count(),
            "count_week": base_queryset.filter(
                created_at__gte=now - timedelta(days=7)
            ).count(),
            "count_month": base_queryset.filter(
                created_at__gte=now - timedelta(days=30)
            ).count(),
            "count_3_months": base_queryset.filter(
                created_at__gte=now - timedelta(days=90)
            ).count(),
            "count_6_months": base_queryset.filter(
                created_at__gte=now - timedelta(days=180)
            ).count(),
            "count_year": base_queryset.filter(
                created_at__gte=now - timedelta(days=365)
            ).count(),
        }
        date_after = request.query_params.get("date_after")
        date_before = request.query_params.get("date_before")
        if date_after and date_before:
            stats["count_custom"] = base_queryset.filter(
                created_at__date__gte=date_after, created_at__date__lte=date_before
            ).count()

        serializer = UserSummaryCountsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
