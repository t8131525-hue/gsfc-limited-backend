# inventory/views/QualityTrendView.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils.dateparse import parse_date
from ..models import ParameterDefinition, TestResult, TestRecord
from ..serializers import QualityTrendDataPointSerializer, QualityTrendSerializer


class QualityTrendView(APIView):
    """
    API view to fetch quality trend data for graphing.
    Requires 'version_id', 'parameter_ids', 'start_date', and 'end_date' query parameters.
    """

    permission_classes = [
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    ]

    queryset = (
        TestRecord.objects.none()
    )  

    def get(self, request, *args, **kwargs):
        # 1. Get and validate query parameters from the request
        version_id = request.query_params.get("version_id")
        parameter_ids_str = request.query_params.get("parameter_ids")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not all([version_id, parameter_ids_str, start_date_str, end_date_str]):
            return Response(
                {
                    "error": "Missing required query parameters: version_id, parameter_ids, start_date, end_date"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Convert parameter_ids from a comma-separated string to a list of integers
            parameter_ids = [int(pid) for pid in parameter_ids_str.split(",")]
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid parameter format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Fetch the parameter definitions the user requested
        # We also ensure these parameters actually belong to the specified version
        parameters = ParameterDefinition.objects.filter(
            pk__in=parameter_ids,
            content_type__model="version",  # Ensures param is linked to a Version model
            object_id=version_id,
        )

        if not parameters.exists():
            return Response(
                {"error": "No valid parameters found for the specified version."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3. Fetch the relevant test results and structure the data
        response_data = []
        for param in parameters:
            # Find all TestResults for this parameter within the date range and for the correct version.
            # We filter for 'APPROVED' or 'CLOSED' records as they represent final, valid results.
            data_points = TestResult.objects.filter(
                parameter=param,
                test_record__version_id=version_id,
                test_record__created_at__date__range=[start_date, end_date],
                test_record__status__in=["APPROVED", "CLOSED"],
            ).order_by("test_record__created_at")

            # Use the serializer to format the data
            serializer = QualityTrendSerializer(
                param, context={"data_points": data_points}
            )

            # Manually add the serialized data points to the response
            serialized_data = serializer.data
            serialized_data["data_points"] = QualityTrendDataPointSerializer(
                data_points, many=True
            ).data
            response_data.append(serialized_data)

        return Response(response_data, status=status.HTTP_200_OK)
