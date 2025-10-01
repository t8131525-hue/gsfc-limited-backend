from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Version
# ✅ 1. Import BOTH serializers
from ..serializers import VersionSerializer, VersionNestedSerializer
from django_filters.rest_framework import DjangoFilterBackend

class VersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Product Versions (Specifications).
    """
    queryset = Version.objects.select_related('product', 'created_by').prefetch_related('parameters', 'grades').all().order_by('-created_at')
    # The default serializer for write actions (POST, PUT, PATCH)
    serializer_class = VersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'status', 'is_active']
    pagination_class = None

    # ✅ 2. Add this method to choose the serializer based on the action
    def get_serializer_class(self):
        """
        Choose a serializer based on the request action.
        - Use VersionNestedSerializer for read-only actions ('list', 'retrieve').
        - Use VersionSerializer for write actions.
        """
        if self.action in ['list', 'retrieve']:
            return VersionNestedSerializer
        return VersionSerializer

    @action(detail=True, methods=['post'], url_path='create-new-version')
    def create_new_version(self, request, pk=None):
        """
        Creates a new, DRAFT version from an existing (usually LOCKED) version.
        """
        original_version = self.get_object()
        try:
            new_version = original_version.create_new_version_from_this()
            # Use the correct serializer for the response
            serializer = VersionNestedSerializer(new_version, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)