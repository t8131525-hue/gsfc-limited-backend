from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Version

from ..serializers import VersionSerializer, VersionNestedSerializer
from django_filters.rest_framework import DjangoFilterBackend


class VersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Product Versions (Specifications).
    """

    # queryset = (
    #     Version.objects.select_related("product", "created_by")
    #     .prefetch_related("parameters", "grades", "grades__parameters")
    #     .all()
    #     .order_by("-created_at")
    # )
    serializer_class = VersionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product", "status", "is_active"]
    pagination_class = None

    def get_serializer_class(self):
        """
        Choose a serializer based on the request action.
        - Use VersionNestedSerializer for read-only actions ('list', 'retrieve').
        - Use VersionSerializer for write actions.
        """
        if self.action in ["list", "retrieve"]:
            return VersionNestedSerializer
        return VersionSerializer

    def get_queryset(self):
        """
        Dynamically filters the queryset based on user permissions.
        - Users with 'can_manage_versions' can see all versions.
        - Other authenticated users can ONLY see 'LOCKED' versions.
        """
        user = self.request.user

        # Start with the base queryset
        queryset = (
            Version.objects.select_related("product", "created_by")
            .prefetch_related("parameters", "grades", "grades__parameters")
            .all()
            .order_by("-created_at")
        )

        if not user.has_perm("inventory.can_manage_versions"):
            queryset = queryset.filter(status="LOCKED")

        return queryset

    @action(detail=True, methods=["post"], url_path="create-new-version")
    def create_new_version(self, request, pk=None):
        """
        Creates a new, DRAFT version from an existing (usually LOCKED) version.
        """
        original_version = self.get_object()
        try:
            new_version = original_version.create_new_version_from_this()
            serializer = VersionNestedSerializer(
                new_version, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
