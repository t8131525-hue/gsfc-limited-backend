# product_testing_system/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    """
    A standard pagination class that can be reused across the application.
    It uses 'page' for the page number and 'page_size' for the page size query params.
    """
    page_size = 5  # The default number of items per page
    page_size_query_param = 'page_size'  # Allows client to override page size e.g. ?page_size=50
    max_page_size = 1000  # The maximum page size the client can request

    def get_paginated_response(self, data):
        """
        Overrides the default response to match the structure your frontend expects.
        """
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })