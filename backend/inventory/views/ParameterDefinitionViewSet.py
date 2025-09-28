from rest_framework import viewsets, permissions
from ..models import ParameterDefinition, Version, ProductGrade
from ..serializers import ParameterDefinitionSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
import django_filters

# --- 1. Define a custom filter class ---
class ParameterDefinitionFilter(django_filters.FilterSet):
    version_id = django_filters.NumberFilter(method='filter_by_owner')
    grade_id = django_filters.NumberFilter(method='filter_by_owner')

    class Meta:
        model = ParameterDefinition
        fields = ['version_id', 'grade_id']

    def filter_by_owner(self, queryset, name, value):
        if name == 'version_id':
            content_type = ContentType.objects.get_for_model(Version)
        elif name == 'grade_id':
            content_type = ContentType.objects.get_for_model(ProductGrade)
        else:
            return queryset
        return queryset.filter(content_type=content_type, object_id=value)

# --- 2. Update the ViewSet ---
class ParameterDefinitionViewSet(viewsets.ModelViewSet):
    queryset = ParameterDefinition.objects.all().order_by("name")
    serializer_class = ParameterDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    # Use the new custom filter class
    filterset_class = ParameterDefinitionFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = None