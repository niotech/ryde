"""
Unit tests for the Friendship app.

This module contains comprehensive tests for friendship models, serializers, views,
and API endpoints.
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import Friendship
from .serializers import FriendshipSerializer, FriendshipCreateSerializer

User = get_user_model()


class FriendshipModelTest(TestCase):
    """Test cases for the Friendship model."""

    def setUp(self):
        """Set up test data."""
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

    def test_create_friendship(self):
        """Test friendship creation."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        self.assertEqual(friendship.from_user, self.user1)
        self.assertEqual(friendship.to_user, self.user2)
        self.assertEqual(friendship.status, 'pending')

    def test_friendship_str_representation(self):
        """Test friendship string representation."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        expected = f"{self.user1.name} -> {self.user2.name} (pending)"
        self.assertEqual(str(friendship), expected)

    def test_friendship_validation_self_friend(self):
        """Test that users cannot be friends with themselves."""
        with self.assertRaises(Exception):
            Friendship.objects.create(
                from_user=self.user1,
                to_user=self.user1,
                status='pending'
            )

    def test_friendship_validation_duplicate(self):
        """Test that duplicate friendships are not allowed."""
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        with self.assertRaises(Exception):
            Friendship.objects.create(
                from_user=self.user1,
                to_user=self.user2,
                status='accepted'
            )

    def test_friendship_properties(self):
        """Test friendship properties."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        self.assertTrue(friendship.is_pending)
        self.assertFalse(friendship.is_accepted)
        self.assertFalse(friendship.is_blocked)

        friendship.status = 'accepted'
        friendship.save()

        self.assertTrue(friendship.is_accepted)
        self.assertFalse(friendship.is_pending)

    def test_friendship_actions(self):
        """Test friendship actions."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        # Test accept
        friendship.accept()
        self.assertEqual(friendship.status, 'accepted')
        self.assertIsNotNone(friendship.accepted_at)

        # Test block
        friendship.block()
        self.assertEqual(friendship.status, 'blocked')

        # Test unblock
        friendship.unblock()
        self.assertEqual(friendship.status, 'pending')

    def test_get_friends(self):
        """Test getting user's friends."""
        # Create accepted friendship
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        friends = Friendship.get_friends(self.user1)
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0], self.user2)

        friends = Friendship.get_friends(self.user2)
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0], self.user1)

    def test_get_followers(self):
        """Test getting user's followers."""
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        followers = Friendship.get_followers(self.user2)
        self.assertEqual(len(followers), 1)
        self.assertEqual(followers[0], self.user1)

    def test_get_following(self):
        """Test getting users that a user is following."""
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        following = Friendship.get_following(self.user1)
        self.assertEqual(len(following), 1)
        self.assertEqual(following[0], self.user2)

    def test_are_friends(self):
        """Test checking if two users are friends."""
        self.assertFalse(Friendship.are_friends(self.user1, self.user2))

        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        self.assertTrue(Friendship.are_friends(self.user1, self.user2))


class FriendshipSerializerTest(TestCase):
    """Test cases for Friendship serializers."""

    def setUp(self):
        """Set up test data."""
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
        self.user3 = User.objects.create_user(
            'user3@example.com',
            name='User 3',
            password='pass123'
        )
        self.friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/api/friendships/', {}, format='json')
        self.request.user = self.user1

    def test_friendship_serializer(self):
        """Test FriendshipSerializer."""
        serializer = FriendshipSerializer(self.friendship)
        data = serializer.data

        self.assertEqual(data['from_user']['id'], str(self.user1.id))
        self.assertEqual(data['to_user']['id'], str(self.user2.id))
        self.assertEqual(data['status'], 'pending')

    def test_friendship_create_serializer(self):
        """Test FriendshipCreateSerializer."""
        data = {
            'to_user': str(self.user3.id),
        }
        serializer = FriendshipCreateSerializer(data=data, context={'request': self.request})
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())

    def test_friendship_create_serializer_self_friend(self):
        """Test FriendshipCreateSerializer with self-friend attempt."""
        data = {
            'to_user': str(self.user1.id),
        }
        serializer = FriendshipCreateSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())


class FriendshipAPITest(APITestCase):
    """Test cases for Friendship API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test users
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
        self.user3 = User.objects.create_user(
            'user3@example.com',
            name='User 3',
            password='pass123'
        )

        # Create tokens and authenticate
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')

    def test_create_friendship_request(self):
        """Test creating a friendship request."""
        url = reverse('friendship-list')
        data = {'to_user': self.user2.id}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Friendship.objects.count(), 1)

    def test_create_friendship_request_to_self(self):
        """Test creating a friendship request to oneself."""
        url = reverse('friendship-list')
        data = {'to_user': self.user1.id}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_my_friendships(self):
        """Test getting user's friendships."""
        # Create some friendships
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )
        Friendship.objects.create(
            from_user=self.user3,
            to_user=self.user1,
            status='accepted'
        )

        url = reverse('friendship-my-friendships')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['friendships']), 2)

    def test_get_pending_requests(self):
        """Test getting pending friendship requests."""
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )

        url = reverse('friendship-pending-requests')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['pending_requests']), 1)

    def test_get_sent_requests(self):
        """Test getting sent friendship requests."""
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        url = reverse('friendship-sent-requests')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['sent_requests']), 1)

    def test_get_friends(self):
        """Test getting user's friends."""
        # Create accepted friendships
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )
        Friendship.objects.create(
            from_user=self.user3,
            to_user=self.user1,
            status='accepted'
        )

        # Debug: Check what friendships exist
        all_friendships = Friendship.objects.all()
        print(f"All friendships in DB: {list(all_friendships.values('from_user__name', 'to_user__name', 'status'))}")

        # Debug: Check what get_friends returns
        friends = Friendship.get_friends(self.user1)
        print(f"Friends returned by get_friends: {list(friends.values('name', 'email'))}")

        url = reverse('friendship-friends')
        response = self.client.get(url)
        print(f"Friends API Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['friends']), 2)

    def test_friendship_status(self):
        """Test getting friendship status."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        url = reverse('friendship-status') + f'?user_id={self.user2.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['friendship_status'], 'pending')

    def test_friendship_action_accept(self):
        """Test accepting a friendship request."""
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )

        url = reverse('friendship-perform-action', args=[friendship.id])
        data = {'action': 'accept'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

    def test_friendship_action_decline(self):
        """Test declining a friendship request."""
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )

        url = reverse('friendship-perform-action', args=[friendship.id])
        data = {'action': 'decline'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'declined')

    def test_friendship_action_block(self):
        """Test blocking a friendship."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='pending'
        )

        url = reverse('friendship-perform-action', args=[friendship.id])
        data = {'action': 'block'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'blocked')

    def test_nearby_friends_with_location(self):
        """Test getting nearby friends with location."""
        # Set user locations
        self.user1.latitude = Decimal('40.7128')
        self.user1.longitude = Decimal('-74.0060')
        self.user1.save()

        self.user2.latitude = Decimal('40.7129')
        self.user2.longitude = Decimal('-74.0061')
        self.user2.save()

        # Create friendship
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        url = reverse('friendship-nearby-friends')
        response = self.client.get(url)
        print(f"Nearby Friends API Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nearby_friends']), 1)

    def test_nearby_friends_without_location(self):
        """Test getting nearby friends without location."""
        # Create friendship without location
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        url = reverse('friendship-nearby-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_friends(self):
        """Test searching friends."""
        # Create friendship
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status='accepted'
        )

        url = reverse('friendship-search-friends') + '?q=User'
        response = self.client.get(url)
        print(f"Search Friends API Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_friendship_permissions(self):
        """Test friendship permissions."""
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user3,
            status='pending'
        )

        # User1 should not be able to access friendship between user2 and user3
        url = reverse('friendship-detail', args=[friendship.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_friendship_list_authenticated(self):
        """Test friendship list with authentication."""
        url = reverse('friendship-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friendship_list_unauthenticated(self):
        """Test friendship list without authentication."""
        self.client.credentials()
        url = reverse('friendship-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
