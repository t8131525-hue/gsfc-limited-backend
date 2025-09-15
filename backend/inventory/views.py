# # inventory/views.py
# from rest_framework import viewsets, permissions, status
# from audit_trail.utils import log_custom_event  # Add this import at the top of the file
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django.utils import timezone  # Import timezone for approval timestamp
# from .models import Product, ParameterDefinition, TestRecord, TestResult

# from rest_framework.views import APIView
# from django.contrib.contenttypes.models import ContentType
# from audit_trail.models import AuditLog
# from audit_trail.request import get_current_request  # To get IP address if needed
# from django_filters.rest_framework import DjangoFilterBackend
# from django.db.models import Q
# from django.db import transaction
# from product_testing_system.pagination import StandardResultsSetPagination
# from rest_framework.filters import SearchFilter, OrderingFilter
# from .filters import TestRecordFilter

# # --- Existing ViewSets ---

# from django.contrib.auth import get_user_model  # <-- Import User model

# User = get_user_model()  # <-- Get User model

