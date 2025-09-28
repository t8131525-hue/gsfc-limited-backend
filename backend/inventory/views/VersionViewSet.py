from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Version
from ..serializers import VersionSerializer # Use the main serializer for C/R/U/D
from django_filters.rest_framework import DjangoFilterBackend

class VersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Product Versions (Specifications).
    """
    queryset = Version.objects.select_related('product', 'created_by').all().order_by('-created_at')
    serializer_class = VersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # Corrected filter fields for the Version model
    filterset_fields = ['product', 'status', 'is_active']
    pagination_class = None

    @action(detail=True, methods=['post'], url_path='create-new-version')
    def create_new_version(self, request, pk=None):
        """
        Creates a new, DRAFT version from an existing (usually LOCKED) version.
        """
        original_version = self.get_object()
        try:
            # Use the corrected method name from the model
            new_version = original_version.create_new_version_from_this()
            serializer = self.get_serializer(new_version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)