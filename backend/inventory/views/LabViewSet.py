# inventory/views/LabViewSet.py

from rest_framework import viewsets, permissions
from ..models import Lab
from ..serializers import LabSerializer

class LabViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows labs to be viewed.
    """
    queryset = Lab.objects.all().order_by('name')
    serializer_class = LabSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None # Return all labs, not paginated