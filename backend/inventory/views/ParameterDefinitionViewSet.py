from rest_framework import viewsets, permissions
from ..models import ParameterDefinition
from django_filters.rest_framework import DjangoFilterBackend
from ..serializers import ParameterDefinitionSerializer


class ParameterDefinitionViewSet(viewsets.ModelViewSet):
    queryset = ParameterDefinition.objects.all().order_by("name")
    serializer_class = ParameterDefinitionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filterset_fields = ["product", "product_grade"]
    filter_backends = [DjangoFilterBackend]
    pagination_class = None 