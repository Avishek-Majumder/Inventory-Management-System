from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class AccountApiTests(APITestCase):
    def test_registration_creates_profile_and_normalizes_email(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'new-user',
            'email': 'NEW@EXAMPLE.COM',
            'password': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='new-user')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(hasattr(user, 'profile'))

    def test_login_and_nested_profile_update(self):
        user = User.objects.create_user('member', 'member@example.com', 'ComplexPass123!')
        login = self.client.post('/api/auth/login/', {
            'username': 'member', 'password': 'ComplexPass123!',
        }, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.patch('/api/auth/me/', {
            'first_name': 'Member',
            'profile': {'phone_number': '+880 1712-345678', 'bio': 'Inventory operator'},
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.profile.bio, 'Inventory operator')

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user('existing', 'existing@example.com', 'ComplexPass123!')
        response = self.client.post('/api/auth/register/', {
            'username': 'another', 'email': 'EXISTING@example.com',
            'password': 'ComplexPass123!', 'password2': 'ComplexPass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
