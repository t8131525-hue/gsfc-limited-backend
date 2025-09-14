from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from audit_trail.models import AuditLog

User = get_user_model()

class AuthenticationTestCase(APITestCase):

    def test_user_login_and_audit(self):
        """
        Ensure a registered user can log in and the event is audited.
        """
        user = User.objects.create_user(username='testlogin', password='password123')
        
        url = '/api/auth/token/' 
        data = {'username': 'testlogin', 'password': 'password123'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        self.assertTrue(AuditLog.objects.filter(user=user, action_type='LOGIN').exists())

    def test_user_detail_view(self):
        """
        Ensure only an authenticated user can view their own details.
        """
        user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=user)
        
        url = '/api/auth/user/'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)

        self.client.logout()
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_user_logout_and_token_blacklist(self):
        """
        Ensure a user can log out, the event is audited, and the refresh token is blacklisted.
        """
        user = User.objects.create_user(username='testlogout', password='password123')
        
        login_response = self.client.post('/api/auth/token/', {'username': 'testlogout', 'password': 'password123'}, format='json')
        refresh_token = login_response.data['refresh']
        
        logout_url = '/api/auth/logout/'
        self.client.force_authenticate(user=user)
        response = self.client.post(logout_url, {'refresh_token': refresh_token}, format='json')

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        
        self.assertTrue(AuditLog.objects.filter(user=user, action_type='LOGOUT').exists())
        
        refresh_url = '/api/auth/token/refresh/'
        response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)