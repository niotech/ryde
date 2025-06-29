"""
Unit tests for the User app.

This module contains comprehensive tests for user models, serializers, views,
and API endpoints.
"""

import json
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import User
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'testpass123',
            'dob': date(1990, 1, 1),
            'address': '123 Test St, Test City',
            'description': 'Test user description',
            'latitude': Decimal('40.7128'),
            'longitude': Decimal('-74.0060'),
        }

    def test_create_user(self):
        """Test user creation."""
        user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
            dob=self.user_data['dob'],
            address=self.user_data['address'],
            description=self.user_data['description'],
            latitude=self.user_data['latitude'],
            longitude=self.user_data['longitude'],
        )
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.name, self.user_data['name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test superuser creation."""
        user = User.objects.create_superuser(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
        )
        expected = f"{user.name} ({user.email})"
        self.assertEqual(str(user), expected)

    def test_age_property(self):
        """Test age calculation property."""
        user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
            dob=self.user_data['dob'],
        )
        expected_age = (date.today() - self.user_data['dob']).days // 365
        self.assertAlmostEqual(user.age, expected_age, delta=1)

    def test_has_location_property(self):
        """Test location availability property."""
        user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
            latitude=self.user_data['latitude'],
            longitude=self.user_data['longitude'],
        )
        self.assertTrue(user.has_location)

        user.latitude = None
        user.longitude = None
        self.assertFalse(user.has_location)

    def test_get_location_tuple(self):
        """Test location tuple retrieval."""
        user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
            latitude=self.user_data['latitude'],
            longitude=self.user_data['longitude'],
        )
        location = user.get_location_tuple()
        self.assertEqual(location, (40.7128, -74.0060))

    def test_invalid_coordinates(self):
        """Test coordinate validation."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                'invalid@example.com',
                name='Invalid User',
                password='testpass123',
                latitude=Decimal('100.0'),  # Invalid latitude
            )


class UserSerializerTest(TestCase):
    """Test cases for User serializers."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'testpass123',
            'dob': date(1990, 1, 1),
            'address': '123 Test St, Test City',
            'description': 'Test user description',
            'latitude': Decimal('40.7128'),
            'longitude': Decimal('-74.0060'),
        }
        self.user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
            dob=self.user_data['dob'],
            address=self.user_data['address'],
            description=self.user_data['description'],
            latitude=self.user_data['latitude'],
            longitude=self.user_data['longitude'],
        )

    def test_user_serializer(self):
        """Test UserSerializer."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['name'], self.user.name)
        self.assertIn('age', data)
        self.assertIn('has_location', data)
        self.assertNotIn('password', data)

    def test_user_create_serializer_valid(self):
        """Test UserCreateSerializer with valid data."""
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'dob': '1995-05-15',
            'address': '456 New St, New City',
            'description': 'New user description',
            'latitude': '41.8781',
            'longitude': '-87.6298',
        }

        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_user_create_serializer_invalid_password(self):
        """Test UserCreateSerializer with mismatched passwords."""
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
        }

        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_user_update_serializer(self):
        """Test UserUpdateSerializer."""
        data = {
            'name': 'Updated Name',
            'address': 'Updated Address',
        }

        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_user = serializer.save()
        self.assertEqual(updated_user.name, 'Updated Name')
        self.assertEqual(updated_user.address, 'Updated Address')


class UserAPITest(APITestCase):
    """Test cases for User API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'testpass123',
        }
        self.user = User.objects.create_user(
            self.user_data['email'],
            name=self.user_data['name'],
            password=self.user_data['password'],
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('user-list')
        data = {
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_user_login(self):
        """Test user login endpoint."""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        url = reverse('user-login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_profile(self):
        """Test getting user profile."""
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user_profile(self):
        """Test updating user profile."""
        url = reverse('user-detail', args=[self.user.id])
        data = {'name': 'Updated Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_user_list_authenticated(self):
        """Test user list endpoint with authentication."""
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_unauthenticated(self):
        """Test user list endpoint without authentication."""
        self.client.credentials()
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password(self):
        """Test password change endpoint."""
        url = reverse('user-change-password')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_users(self):
        """Test user search functionality."""
        url = reverse('user-search-by-name') + '?q=Test'
        response = self.client.get(url)
        print(f"Search Users API Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_nearby_users_without_location(self):
        """Test nearby users without user location."""
        url = reverse('user-nearby-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearby_users_with_location(self):
        """Test nearby users with user location."""
        # Update user with location
        self.user.latitude = Decimal('40.7128')
        self.user.longitude = Decimal('-74.0060')
        self.user.save()

        # Create nearby user
        User.objects.create_user(
            'nearby@example.com',
            name='Nearby User',
            password='nearby123',
            latitude=Decimal('34.0522'),
            longitude=Decimal('-118.2437'),
        )

        url = reverse('user-nearby-friends')
        response = self.client.get(url)
        print(f"Nearby Users API Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nearby_users']), 1)

    def test_user_logout(self):
        """Test user logout endpoint."""
        url = reverse('user-logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_user(self):
        """Test user deletion endpoint."""
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)


class UserPermissionsTest(APITestCase):
    """Test cases for user permissions."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            'user1@example.com',
            name='User 1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            'user2@example.com',
            name='User 2',
            password='pass123'
        )
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

    def test_user_cannot_update_other_user(self):
        """Test that users cannot update other users' profiles."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('user-detail', args=[self.user2.id])
        data = {'name': 'Hacked Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_other_user(self):
        """Test that users cannot delete other users."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('user-detail', args=[self.user2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
