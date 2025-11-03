from rest_framework.views import APIView
from rest_framework import permissions
from ..models import Product, TestRecord
from rest_framework.response import Response


class InventoryStatsView(APIView):
    """
    A dedicated view to provide key statistics for the inventory dashboard.
    """

    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]

    def get(self, request, *args, **kwargs):
        total_products = Product.objects.count()
        pending_tests = TestRecord.objects.filter(status="PENDING").count()

        stats = {
            "total_products": total_products,
            "pending_tests": pending_tests,
        }
        return Response(stats)
