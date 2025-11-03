# authentication/urls.py
from django.urls import path, include # ✅ 1. Import include
from rest_framework.routers import DefaultRouter # ✅ 2. Import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    LogoutView,
    UserDetailView,
    UserViewSet, # ✅ 3. Import UserViewSet
)

# ✅ 4. CREATE A ROUTER AND REGISTER THE VIEWSET
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# ✅ 5. UPDATE urlpatterns
urlpatterns = [
    # URLs for token management and the current user
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserDetailView.as_view(), name='user_detail'),
    
    # Include the router's URLs. This automatically creates:
    # /api/auth/users/ (for the list)
    # /api/auth/users/<pk>/ (for a single user)
    path('', include(router.urls)),
]