# authentication/views.py
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserDetailSerializer
from audit_trail.utils import log_custom_event
from rest_framework_simplejwt.exceptions import TokenError
import logging 

User = get_user_model()

logger = logging.getLogger(__name__)

class IsManagerOrSupervisor(permissions.BasePermission):
    """
    Custom permission to only allow access to managers or supervisors.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and has the required role
        return request.user and request.user.is_authenticated and request.user.role in ['manager', 'supervisor','admin']
    
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view to add audit logging."""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            try:
                user = User.objects.get(username=request.data['username'])
                details = {"message": f"User '{user.username}' obtained JWT token."}
                log_custom_event(instance=user, action_type='LOGIN', details=details, user=user)
            except User.DoesNotExist:
                pass # Should not fail if login was successful
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
            # Get the refresh token from the request body
            refresh_token = request.data["refresh_token"]
            
            # Create a RefreshToken instance and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log the logout event for the audit trail
            details = {"message": f"User '{request.user.username}' logged out successfully."}
            log_custom_event(instance=request.user, action_type='LOGOUT', details=details, user=request.user)
            
            return Response(status=status.HTTP_205_RESET_CONTENT)

        except TokenError:
            # This will catch errors if the token is invalid, expired, or already blacklisted
            return Response({"error": "Token is invalid or expired"}, status=status.HTTP_401_UNAUTHORIZED)
            
        except KeyError:
            # This will catch an error if 'refresh_token' is not in the request body
            return Response({"error": "refresh_token not provided"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"An unexpected error occurred during logout for user '{request.user.username}': {e}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListAPIView):
    """
    A view that returns a list of all 'analyst' users.
    Only accessible by users with the 'manager' or 'supervisor' role.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrSupervisor] # Use our new permission

    def get_queryset(self):
        """
        This view should only return users with the 'analyst' role.
        """
        return User.objects.filter(role='analyst').order_by('username')