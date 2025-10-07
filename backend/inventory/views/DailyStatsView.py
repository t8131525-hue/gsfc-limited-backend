# inventory/views/DailyStatsView.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from ..models import TestRecord
from ..serializers import DailyStatsSerializer


class DailyStatsView(APIView):
    """
    Provides statistics for test records created today.
    - total_tests: All records for the day.
    - pending_tests: Records with 'PENDING' status.
    - approved_tests: Records with 'APPROVED' status.
    - rejected_tests: Records with 'REJECTED' status.
    The counts respect user permissions (analysts see their own stats,
    managers see all).
    """

    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = timezone.now().date()

        # Start with the base queryset for today's records
        queryset = TestRecord.objects.filter(created_at__date=today)

        # Apply permission-based filtering
        if not user.has_perm("inventory.can_view_all_test_records"):
            queryset = queryset.filter(analyst=user)

        # Calculate stats efficiently in the database
        stats_data = {
            "total_tests": queryset.count(),
            "pending_tests": queryset.filter(status="PENDING").count(),
            "approved_tests": queryset.filter(status="APPROVED").count(),
            "rejected_tests": queryset.filter(status="REJECTED").count(),
        }

        serializer = DailyStatsSerializer(data=stats_data)
        serializer.is_valid(raise_exception=True)  # Ensure data matches serializer
        return Response(serializer.data)
