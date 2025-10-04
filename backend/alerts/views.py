# alerts/views.py
from .models import Alert
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import AlertSerializer, AlertContextSerializer
from product_testing_system.pagination import StandardResultsSetPagination
from django.utils import timezone
from django.db import transaction


# --- UPDATED: No longer a ReadOnlyModelViewSet ---
class AlertViewSet(viewsets.ModelViewSet):
    """
    An API endpoint for viewing and managing alerts.
    - GET: /api/alerts/ (Filter by status, e.g., ?status=NEW)
    - PATCH: /api/alerts/{id}/update_status/
    """

    queryset = (
        Alert.objects.select_related(
            "test_record__version__product",
            "test_record__product_grade",
            "test_record__analyst",
            "test_record__lab",
        )
        .all()
        .order_by("-created_at")
    )

    serializer_class = AlertSerializer

    # permissions.IsAuthenticated is safer for managing alerts
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filter_backends = [DjangoFilterBackend]
    # --- NEW: Allow filtering by multiple statuses ---
    filterset_fields = {
        "status": ["exact", "in"],
        "test_record": ["exact"],
    }

    # --- Make the ViewSet mostly read-only except for our custom action ---
    http_method_names = ["get", "head", "options", "patch"]

    def get_serializer_class(self):
        """Return different serializers for different actions."""
        if self.action == "context":
            return AlertContextSerializer
        return AlertSerializer

    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        """
        Custom action to update the status of an alert.
        """
        # ✅ FIX: Wrap the entire logic in a transaction
        with transaction.atomic():
            alert = Alert.objects.select_for_update().get(pk=pk)
            new_status = request.data.get("status")
            user = request.user

            valid_statuses = [choice[0] for choice in Alert.STATUS_CHOICES]
            if not new_status or new_status not in valid_statuses:
                return Response(
                    {
                        "error": f"Invalid status provided. Choose from: {valid_statuses}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if alert.status == "RESOLVED":
                return Response(
                    {"detail": "This alert has already been resolved."},
                    status=status.HTTP_409_CONFLICT,
                )

            update_fields = ["status"]
            if new_status == "ACKNOWLEDGED" and not alert.acknowledged_by:
                alert.acknowledged_by = user
                alert.acknowledged_at = timezone.now()
                update_fields.extend(["acknowledged_by", "acknowledged_at"])
            elif new_status == "RESOLVED" and not alert.resolved_by:
                alert.resolved_by = user
                alert.resolved_at = timezone.now()
                if not alert.acknowledged_by:
                    alert.acknowledged_by = user
                    alert.acknowledged_at = timezone.now()
                    update_fields.extend(["acknowledged_by", "acknowledged_at"])
                update_fields.extend(["resolved_by", "resolved_at"])

            alert.status = new_status
            alert.save(update_fields=update_fields)

        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=["get"], url_path="context")
    def context(self, request, pk=None):
        """
        Returns the full context for an alert, including the
        entire test record and all of its results.
        """
        alert = self.get_object()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
