# authentication/views.py
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserDetailSerializer, CustomTokenObtainPairSerializer
from audit_trail.utils import log_custom_event
from rest_framework_simplejwt.exceptions import TokenError
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


# --- New Permission Class ---
class HasRequiredPermission(permissions.BasePermission):
    """
    Custom permission to check if a user has a specific permission codename.
    The view using this permission must define a 'required_permission' attribute.
    e.g., required_permission = 'authentication.view_analyst_list'
    """

    def has_permission(self, request, view):
        # Get the required permission from the view, or deny access if not specified.
        required_perm = getattr(view, "required_permission", None)
        if not required_perm:
            return False

        # Check if the user is authenticated and has the permission.
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_perm(required_perm)
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view to add audit logging."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            try:
                user = User.objects.get(username=request.data["username"])
                details = {"message": f"User '{user.username}' obtained JWT token."}
                log_custom_event(
                    instance=user, action_type="LOGIN", details=details, user=user
                )
            except User.DoesNotExist:
                pass
        return response


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            details = {
                "message": f"User '{request.user.username}' logged out successfully."
            }
            log_custom_event(
                instance=request.user,
                action_type="LOGOUT",
                details=details,
                user=request.user,
            )
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response(
                {"error": "Token is invalid or expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except KeyError:
            return Response(
                {"error": "refresh_token not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during logout for user '{request.user.username}': {e}"
            )
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserListView(generics.ListAPIView):
    """
    A view that returns a list of all 'analyst' users.
    Only accessible by users with the 'view_analyst_list' permission.
    """

    serializer_class = UserDetailSerializer
    # Use the new permission class
    permission_classes = [permissions.IsAuthenticated, HasRequiredPermission]
    # Specify the single required permission codename (app_label.codename)
    required_permission = "authentication.view_user_list"

    def get_queryset(self):
        """
        This view should now return users who are in the 'Analyst' group.
        """
        return User.objects.filter(groups__name="Analyst").order_by("username")
