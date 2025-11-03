from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Version

# ✅ 1. Import your new VersionListSerializer
from ..serializers import VersionSerializer, VersionNestedSerializer, VersionListSerializer
from django_filters.rest_framework import DjangoFilterBackend


class VersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Product Versions (Specifications).
    """

    serializer_class = VersionSerializer  # Default for write actions
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product", "status", "is_active"]
    pagination_class = None

    # ✅ 2. Update this method to use VersionListSerializer
    def get_serializer_class(self):
        """
        Dynamically choose the serializer.
        - Use VersionListSerializer for 'list' (lightweight)
        - Use VersionNestedSerializer for 'retrieve' (detailed)
        - Use VersionSerializer for write actions.
        """
        if self.action == 'list':
            return VersionListSerializer
        if self.action in ["retrieve"]:
            return VersionNestedSerializer
        return self.serializer_class # This is VersionSerializer

    # ✅ 3. Update this method to be more efficient
    def get_queryset(self):
        """
        Dynamically filters and optimizes the queryset.
        - Only performs heavy prefetching for 'retrieve' action.
        """
        user = self.request.user

        # Start with a simpler base queryset
        queryset = Version.objects.select_related("product", "created_by")

        # ✅ Only add heavy prefetch if we're retrieving a single, nested item
        if self.action == 'retrieve':
             queryset = queryset.prefetch_related(
                 "parameters", "grades", "grades__parameters"
             )

        # Apply permission-based filtering
        if not user.has_perm("inventory.can_manage_versions"):
            queryset = queryset.filter(status="LOCKED")

        # Apply ordering and filtering from the request
        # The filterset_fields will still work correctly on this.
        return queryset.all().order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="create-new-version")
    def create_new_version(self, request, pk=None):
        """
        Creates a new, DRAFT version from an existing (usually LOCKED) version.
        """
        original_version = self.get_object()
        try:
            new_version = original_version.create_new_version_from_this()
            # Using VersionNestedSerializer here is fine, as it's a single item
            serializer = VersionNestedSerializer(
                new_version, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)