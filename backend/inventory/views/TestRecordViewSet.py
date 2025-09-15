from rest_framework import viewsets, permissions
from ..models import TestRecord
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers import TestRecordSerializer
from product_testing_system.pagination import StandardResultsSetPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from ..filters import TestRecordFilter
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
# Add all of these at the top of the file
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from audit_trail.utils import log_custom_event
from ..serializers.AssignAnalystSerializer import AssignAnalystSerializer

User = get_user_model()

class TestRecordViewSet(viewsets.ModelViewSet):
    """
    Manages Test Records, including creation, approval, rejection,
    and ordering of retests.
    """

    queryset = TestRecord.objects.all().order_by("-created_at")
    serializer_class = TestRecordSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TestRecordFilter
    filterset_fields = ["product", "product_grade", "analyst", "status"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "analyst"]
    search_fields = ["sample_id", "batch_no", "product__name", "record_id"]
    ordering_fields = ["created_at", "analyst__username", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Dynamically filters the queryset based on user permissions.
        - Users with 'can_view_all_test_records' see all records.
        - Other users (e.g., analysts) only see records assigned to them.
        """
        user = self.request.user

        # Start with an optimized base queryset
        queryset = (
            TestRecord.objects.select_related(
                "product", "product_grade", "analyst", "approved_by", "retest_of"
            )
            .prefetch_related("parameter_values__parameter")
            .all()
        )

        # If the user does NOT have the permission to view all records,
        # filter the queryset to only show records assigned to them.
        if not user.has_perm("inventory.can_view_all_test_records"):
            queryset = queryset.filter(analyst=user)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

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
        """
        Orders a retest and assigns it to a specific analyst.
        This creates a new PENDING_RETEST test record and updates the
        original record's status to RETEST_ORDERED.
        """
        user = request.user
        if not user.has_perm("inventory.can_approve_test_records"):
            return Response(
                {"detail": "You do not have permission to order a retest."},
                status=status.HTTP_403_FORBIDDEN,
            )

        original_test = self.get_object()

        if original_test.status not in ["APPROVED", "REJECTED"]:
            return Response(
                {
                    "detail": f"Can only order a retest for a record that is 'APPROVED' or 'REJECTED'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the incoming analyst_id using our serializer
        serializer = AssignAnalystSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        analyst_id = serializer.validated_data["analyst_id"]
        analyst_to_assign = User.objects.get(pk=analyst_id)

        with transaction.atomic():
            # 1. Update the original record's status
            original_test.status = "RETEST_ORDERED"
            original_test.save()

            # 2. Create the new TestRecord for the retest, now with an analyst
            new_test = TestRecord.objects.create(
                product=original_test.product,
                product_grade=original_test.product_grade,
                batch_no=original_test.batch_no,
                sample_id=original_test.sample_id,
                status="RETEST",  # Use the new specific status
                analyst=analyst_to_assign,  # Assign the analyst immediately
                retest_of=original_test,
            )

            # 3. Log the event against the original test record
            log_custom_event(
                instance=original_test,
                action_type="RETEST_ORDERED",
                user=user,
                details=f"Retest ordered by {user.username} and assigned to {analyst_to_assign.username}. New record: {new_test.record_id}",
            )

        # Return the newly created test record
        response_serializer = self.get_serializer(new_test)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

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

        test_record = self.get_object()
        new_status = request.data.get("status")
        comments = request.data.get(
            "supervisor_comments", test_record.supervisor_comments
        )

        if new_status not in ["APPROVED", "REJECTED"]:
            return Response(
                {
                    "error": f"Invalid status '{new_status}'. This action only accepts 'APPROVED' or 'REJECTED'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if test_record.status == new_status:
            return Response(
                {"detail": f"Test record is already {new_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = test_record.status
        old_approval_user = (
            str(test_record.approved_by) if test_record.approved_by else ""
        )
        old_comments = (
            test_record.supervisor_comments if test_record.supervisor_comments else ""
        )

        test_record.status = new_status
        test_record.supervisor_comments = comments
        test_record.approved_by = user
        test_record.approved_at = timezone.now()
        test_record.save()

        details = {
            "status": [old_status, new_status],
            "supervisor_comments": [
                old_comments,
                comments if comments is not None else "",
            ],
            "approved_by": [old_approval_user, str(user)],
        }
        log_custom_event(
            instance=test_record, action_type=new_status, details=details, user=user
        )

        serializer = self.get_serializer(test_record)
        return Response(serializer.data)
