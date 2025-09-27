# inventory/views/SpecificationViewSet.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Specification
from ..serializers import SpecificationSerializer
from django_filters.rest_framework import DjangoFilterBackend

class SpecificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Specification Versions.
    """
    queryset = Specification.objects.all().order_by('-version')
    serializer_class = SpecificationSerializer
    permission_classes = [permissions.IsAuthenticated] # Add your specific permissions here
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'product_grade', 'is_active']
    pagination_class = None # Specs are usually not paginated, but you can add it if needed.

    @action(detail=True, methods=['post'], url_path='create-new-version')
    def create_new_version(self, request, pk=None):
        """
        Creates a new, inactive version from an existing specification.
        """
        original_spec = self.get_object()
        try:
            new_spec = original_spec.create_new_version()
            serializer = self.get_serializer(new_spec)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)