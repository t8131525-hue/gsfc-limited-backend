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

        # 1. DETERMINE THE DATE RANGE
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

        # ✅ 2. AUTOMATICALLY DETERMINE THE BEST 'group_by' LEVEL
        duration = end_date - start_date
        group_by = request.query_params.get("group_by", "day")

        # ✅ FIX: CALCULATE THE DATE RANGE BASED ON THE 'group_by' PARAMETER
        end_date = timezone.now().date()
        if group_by == "day":  # Corresponds to "Last 7 Days"
            start_date = end_date - timedelta(days=6)
        elif group_by == "week":  # Corresponds to "Last 30 Days" and "Last 3 Months"
            # Determine if it's 30 or 90 days based on frontend logic
            # For simplicity, we can default to 30 for now, but a more robust
            # solution would be for the frontend to send the date range.
            # Let's assume the frontend will send date_after/date_before for custom ranges.
            # This logic is for the predefined dropdowns.
            if request.query_params.get("range") == "3_months":  # Hypothetical param
                start_date = end_date - timedelta(days=89)
            else:  # Default for 'week' grouping is 30 days
                start_date = end_date - timedelta(days=29)
        elif group_by == "month":  # Corresponds to "Last 6 Months" and "Last Year"
            if request.query_params.get("range") == "year":  # Hypothetical param
                start_date = end_date - timedelta(days=364)
            else:  # Default for 'month' grouping is 6 months
                start_date = end_date - timedelta(days=179)
        else:  # Default case
            start_date = end_date - timedelta(days=6)

        # Override with custom date range if provided
        date_after_str = request.query_params.get("date_after")
        date_before_str = request.query_params.get("date_before")
        if date_after_str and date_before_str:
            try:
                start_date = date.fromisoformat(date_after_str)
                end_date = date.fromisoformat(date_before_str)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ✅ REMOVED: The old logic that was causing the 400 Bad Request error.
        # Now the view handles all group_by types.

        trunc_function = {
            "day": TruncDay,
            "week": TruncWeek,
            "month": TruncMonth,
        }.get(group_by, TruncDay)

        db_counts = (
            TestRecord.objects.filter(
                analyst=user,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .annotate(date=Cast(trunc_function("created_at"), output_field=DateField()))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        # Zero-filling for daily grouping is still a good idea
        if group_by == "day":
            duration = end_date - start_date
            all_dates = {
                (start_date + timedelta(days=i)).isoformat(): 0
                for i in range(duration.days + 1)
            }
            for item in db_counts:
                date_str = item["date"].isoformat()
                if date_str in all_dates:
                    all_dates[date_str] = item["count"]

            chart_data = [
                {"date": date_str, "count": count}
                for date_str, count in all_dates.items()
            ]
        else:
            chart_data = list(db_counts)

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
