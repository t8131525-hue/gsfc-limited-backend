from rest_framework import viewsets, permissions
from ..models import ProductGrade
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers import ProductGradeSerializer


class ProductGradeViewSet(viewsets.ModelViewSet):
    queryset = ProductGrade.objects.all().order_by("product__name", "name")
    serializer_class = ProductGradeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product"]
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
