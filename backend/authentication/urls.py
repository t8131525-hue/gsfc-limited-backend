from django.urls import path
from .views import UserDetailView, LogoutView, CustomTokenObtainPairView, UserListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('users/', UserListView.as_view(), name='user_list'),
    path('user/', UserDetailView.as_view(), name='user_detail'),
    path('logout/', LogoutView.as_view(), name='logout_user'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]