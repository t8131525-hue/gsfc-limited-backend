from rest_framework import viewsets, permissions
from ..models import TestResult
from ..serializers import TestResultDisplaySerializer
from django_filters.rest_framework import DjangoFilterBackend


class TestResultViewSet(viewsets.ModelViewSet):
    queryset = TestResult.objects.all().order_by("parameter__name")
    serializer_class = TestResultDisplaySerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["test_record", "parameter"]
