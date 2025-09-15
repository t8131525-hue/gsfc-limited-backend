from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from ..models import Product
from ..serializers import ProductSerializer
from django_filters.rest_framework import DjangoFilterBackend
from product_testing_system.pagination import StandardResultsSetPagination
from rest_framework.filters import SearchFilter, OrderingFilter


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    @action(detail=True, methods=["get"])
    def parameters(self, request, pk=None):
        """
        A custom endpoint to retrieve all parameter definitions associated
        with a specific product, including parameters linked to its grades.
        """
        product = self.get_object()

        # This query finds all parameters linked directly to the product
        # OR linked to any of the product's grades.
        parameters_queryset = ParameterDefinition.objects.filter(
            Q(product=product) | Q(product_grade__product=product)
        ).distinct()

        serializer = ParameterDefinitionSerializer(parameters_queryset, many=True)
        return Response(serializer.data)
