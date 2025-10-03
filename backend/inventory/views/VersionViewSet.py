from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Version

from ..serializers import VersionSerializer, VersionNestedSerializer
from django_filters.rest_framework import DjangoFilterBackend


class VersionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Product Versions (Specifications).
    """

    queryset = (
        Version.objects.select_related("product", "created_by")
        .prefetch_related("parameters", "grades", "grades__parameters")
        .all()
        .order_by("-created_at")
    )
    serializer_class = VersionSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product", "status", "is_active"]
    pagination_class = None

    def get_serializer_class(self):
        """
        Choose a serializer based on the request action.
        - Use VersionNestedSerializer for read-only actions ('list', 'retrieve').
        - Use VersionSerializer for write actions.
        """
        if self.action in ["list", "retrieve"]:
            return VersionNestedSerializer
        return VersionSerializer

    @action(detail=True, methods=["post"], url_path="create-new-version")
    def create_new_version(self, request, pk=None):
        """
        Creates a new, DRAFT version from an existing (usually LOCKED) version.
        """
        original_version = self.get_object()
        try:
            new_version = original_version.create_new_version_from_this()
            serializer = VersionNestedSerializer(
                new_version, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
User = get_user_model()
username_to_check = 'analyst1'
print(f"--- Verifying Permissions for user: '{username_to_check}' ---")
try:
    user = User.objects.get(username=username_to_check)
    print(f"\n✅ User '{user.username}' found (ID: {user.id}).")
    user_groups = user.groups.all()
    if user_groups:
        group_names = ", ".join([group.name for group in user_groups])
        print(f"✅ User is in {user_groups.count()} group(s): {group_names}")
    else:
        print(f"❌ User is in ZERO groups.")
    permission_to_check = 'inventory.add_version'
    has_perm = user.has_perm(permission_to_check)
    print(f"\n--- Checking for Create Version Permission ('{permission_to_check}') ---")
    if has_perm:
        print(f"✅ RESULT: User '{user.username}' HAS the permission to create versions.")
    else:
        print(f"✅ RESULT: User '{user.username}' does NOT have the permission to create versions.")
    print("\n--- Full List of All Permissions ---")
    all_perms = sorted(list(user.get_all_permissions()))
    if all_perms:
        for perm in all_perms:
            print(f"  - {perm}")
    else:
        print("  User has NO permissions assigned directly or via groups.")
except User.DoesNotExist:
    print(f"\n❌ ERROR: User '{username_to_check}' was not found in the database.")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")
print("\n--- Verification Complete ---")