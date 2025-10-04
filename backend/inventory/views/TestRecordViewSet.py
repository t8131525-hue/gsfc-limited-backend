from rest_framework import viewsets, permissions
from ..models import TestRecord
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers import TestRecordSerializer
from product_testing_system.pagination import StandardResultsSetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from ..filters import TestRecordFilter
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from ..serializers import (
    TestRecordSerializer,
    RecentTestRecordSerializer,
    HistoricalTestRecordSerializer,
)

# Add all of these at the top of the file
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from audit_trail.utils import log_custom_event
from ..serializers.AssignAnalystSerializer import AssignAnalystSerializer

User = get_user_model()


class TestRecordViewSet(viewsets.ModelViewSet):
    # The base queryset is simple; logic is moved to get_queryset
    queryset = TestRecord.objects.all()
    # The default serializer for retrieve/create/update actions
    serializer_class = TestRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TestRecordFilter
    search_fields = ["sample_id", "batch_no", "version__product__name", "record_id"]
    ordering_fields = ["created_at", "analyst__username", "status", "lab__name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Dynamically filters the queryset.
        - Non-managers only see their own records.
        - The 'Recent' view is automatically filtered for today's date.
        """
        user = self.request.user
        view_type = self.request.query_params.get("view_type", "recent")

        # Base queryset with performance optimizations
        queryset = TestRecord.objects.select_related(
            "version__product", "product_grade", "analyst", "lab"
        ).all()

        # Permission-based filtering
        if not user.has_perm("inventory.can_view_all_test_records"):
            queryset = queryset.filter(analyst=user)

        # Automatic date filtering for the "Recent" view
        if self.action == "list" and view_type == "recent":
            today = timezone.now().date()
            queryset = queryset.filter(created_at__date=today)

        return queryset

    def get_serializer_class(self):
        """
        Chooses the serializer based on the action and view type.
        - 'list' action gets a lightweight serializer.
        - Other actions (retrieve, create, update) get the full serializer.
        """
        if self.action == "list":
            view_type = self.request.query_params.get("view_type", "recent")
            if view_type == "historical":
                return HistoricalTestRecordSerializer
            return RecentTestRecordSerializer

        return TestRecordSerializer

    @action(
        detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated]
    )
    def assign(self, request, pk=None):
        """
        Assigns an analyst to an unassigned test record.
        Only accessible by users with approval permissions (Managers/Supervisors).
        """
        user = request.user
        if not user.has_perm("inventory.can_approve_test_records"):
            return Response(
                {"detail": "You do not have permission to assign tests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        test_record = self.get_object()

        if test_record.analyst is not None:
            return Response(
                {"detail": "This test has already been assigned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AssignAnalystSerializer(data=request.data)
        if serializer.is_valid():
            analyst_id = serializer.validated_data["analyst_id"]
            analyst_to_assign = User.objects.get(pk=analyst_id)

            test_record.analyst = analyst_to_assign
            test_record.save()

            log_custom_event(
                instance=test_record,
                action_type="ASSIGNED",
                user=user,
                details=f"Assigned to analyst {analyst_to_assign.username} by {user.username}.",
            )

            return Response(
                self.get_serializer(test_record).data, status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def order_retest(self, request, pk=None):
        user = request.user
        if not user.has_perm("inventory.can_approve_test_records"):
            return Response(
                {"detail": "You do not have permission to order a retest."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            # Lock the original test to prevent simultaneous actions
            original_test = self.get_object()
            if original_test.status not in ["APPROVED", "REJECTED"]:
                return Response(
                    {
                        "detail": "Can only order a retest for a record that is 'APPROVED' or 'REJECTED'."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = AssignAnalystSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            analyst_id = serializer.validated_data["analyst_id"]
            try:
                analyst_to_assign = User.objects.get(pk=analyst_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Selected analyst not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            original_test.status = "RETEST_ORDERED"
            original_test.retest_ordered_by = user
            original_test.retest_ordered_at = timezone.now()
            original_test.save(
                update_fields=["status", "retest_ordered_by", "retest_ordered_at"]
            )

            new_test = TestRecord.objects.create(
                version=original_test.version,
                lab=original_test.lab,
                product_grade=original_test.product_grade,
                batch_no=original_test.batch_no,
                sample_id=original_test.sample_id,
                status="PENDING",
                analyst=analyst_to_assign,
                retest_of=original_test,
            )
            log_custom_event(
                instance=original_test,
                action_type="RETEST_ORDERED",
                user=user,
                details=f"Retest ordered by {user.username} and assigned to {analyst_to_assign.username}. New record: {new_test.record_id}",
            )
        response_serializer = self.get_serializer(new_test)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # Approve/Reject
    @action(
        detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated]
    )
    def approve_reject(self, request, pk=None):
        """
        Approves or rejects a test record. This is a final action.
        """
        user = request.user
        if not user.has_perm("inventory.can_approve_test_records"):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            test_record = TestRecord.objects.select_for_update().get(pk=pk)

            if test_record.status != "PENDING":
                return Response(
                    {
                        "detail": "This record has already been actioned by another user."
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            new_status = request.data.get("status")
            comments = request.data.get(
                "supervisor_comments", test_record.supervisor_comments
            )

            if new_status not in ["APPROVED", "REJECTED"]:
                return Response(
                    {"error": f"Invalid status '{new_status}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            test_record.status = new_status
            test_record.supervisor_comments = comments
            test_record.approved_by = user
            test_record.approved_at = timezone.now()
            test_record.save()

            log_custom_event(
                instance=test_record,
                action_type=new_status,
                details=f"Record status changed to {new_status} by {user.username}.",
                user=user,
            )

        serializer = self.get_serializer(test_record)
        return Response(serializer.data)

    # Close the record
    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def close_record(self, request, pk=None):
        """
        Closes an APPROVED or REJECTED test record. This is a final state.
        """
        user = request.user
        if not user.has_perm("inventory.can_approve_test_records"):
            return Response(
                {"detail": "You do not have permission to close records."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            test_record = TestRecord.objects.select_for_update().get(pk=pk)

            if test_record.status not in ["APPROVED", "REJECTED"]:
                return Response(
                    {
                        "detail": f"Cannot close a record with status '{test_record.status}'. Only 'APPROVED' or 'REJECTED' records can be closed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            old_status = test_record.status
            test_record.status = "CLOSED"
            test_record.closed_by = request.user
            test_record.closed_at = timezone.now()
            test_record.save(update_fields=["status", "closed_by", "closed_at"])

            log_custom_event(
                instance=test_record,
                action_type="CLOSED",
                user=user,
                details=f"Record status changed from {old_status} to CLOSED by {user.username}.",
            )

        serializer = self.get_serializer(test_record)
        return Response(serializer.data, status=status.HTTP_200_OK)
