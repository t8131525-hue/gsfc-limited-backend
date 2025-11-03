from rest_framework import viewsets, permissions
from ..models import ProductGrade
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers import ProductGradeSerializer

class ProductGradeViewSet(viewsets.ModelViewSet):
    # Corrected ordering to go through the version
    queryset = ProductGrade.objects.all().order_by("version__product__name", "name")
    serializer_class = ProductGradeSerializer
    filter_backends = [DjangoFilterBackend]
    # Corrected filter fields
    filterset_fields = ["version", "version__product"]
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]