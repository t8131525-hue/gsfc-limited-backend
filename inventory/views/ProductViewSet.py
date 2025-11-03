from rest_framework import viewsets, permissions
from ..models import Product
from ..serializers import ProductSerializer, ProductListSerializer
from django_filters.rest_framework import DjangoFilterBackend
from product_testing_system.pagination import StandardResultsSetPagination
from rest_framework.filters import SearchFilter, OrderingFilter


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "product_id"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Dynamically filter the queryset.

        - By default, return all products.
        - If 'is_active=true' is in the query params,
          return only products with an active, locked version.
        """
        queryset = super().get_queryset()
        is_active_filter = self.request.query_params.get("is_active")
        if is_active_filter == "true":
            queryset = queryset.filter(versions__is_active=True).distinct()
        return queryset

    def get_serializer_class(self):
        """
        Use the lightweight ProductListSerializer for 'list' actions
        and the full ProductSerializer for 'retrieve'.
        """
        if self.action == "list":
            return ProductListSerializer
        return self.serializer_class

    def get_pagination_class(self):
        """
        Dynamically disable pagination if 'all=true' is in the query params.
        """
        if self.request.query_params.get("all") == "true":
            return None
        return self.pagination_class
