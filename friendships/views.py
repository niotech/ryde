"""
Views for the Friendship API.

This module provides REST API views for friendship management including
CRUD operations, status management, and location-based friend queries.
"""

import logging
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from geopy.distance import geodesic

from .models import Friendship
from .serializers import (
    FriendshipSerializer, FriendshipCreateSerializer, FriendshipUpdateSerializer,
    FriendshipListSerializer, FriendshipStatusSerializer, UserFriendsSerializer,
    NearbyFriendsSerializer, FriendshipActionSerializer
)
from users.models import User
from users.serializers import UserListSerializer

logger = logging.getLogger(__name__)


class FriendshipViewSet(ModelViewSet):
    """
    ViewSet for Friendship model providing CRUD operations.

    This ViewSet handles all friendship-related operations including:
    - Friendship request management
    - Status updates (accept, decline, block)
    - Friend lists and queries
    - Location-based friend searches
    """

    queryset = Friendship.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']  # Removed from_user and to_user as they cause UUID issues during schema generation
    search_fields = ['from_user__name', 'to_user__name']
    ordering_fields = ['created_at', 'updated_at', 'accepted_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return FriendshipCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FriendshipUpdateSerializer
        elif self.action == 'list':
            return FriendshipListSerializer
        elif self.action == 'status':
            return FriendshipStatusSerializer
        elif self.action == 'perform_action':
            return FriendshipActionSerializer
        return FriendshipSerializer

    def get_queryset(self):
        """Return filtered queryset based on user permissions."""
        # Handle schema generation for Swagger/OpenAPI
        if getattr(self, 'swagger_fake_view', False):
            return Friendship.objects.none()

        user = self.request.user

        # Handle anonymous users (should not happen in normal operation due to IsAuthenticated)
        if user.is_anonymous:
            return Friendship.objects.none()

        # Users can only see friendships they're involved in
        return Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related('from_user', 'to_user')

    def perform_create(self, serializer):
        """Create friendship and log the action."""
        friendship = serializer.save()
        logger.info(
            f"Friendship request created: {friendship.from_user.email} -> {friendship.to_user.email}"
        )

    def perform_update(self, serializer):
        """Update friendship and log the action."""
        friendship = serializer.save()
        logger.info(
            f"Friendship updated: {friendship.from_user.email} -> {friendship.to_user.email} "
            f"(Status: {friendship.status})"
        )

    def perform_destroy(self, instance):
        """Delete friendship and log the action."""
        logger.info(
            f"Friendship deleted: {instance.from_user.email} -> {instance.to_user.email}"
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def my_friendships(self, request):
        """
        Get current user's friendships.

        Returns all friendships for the authenticated user.
        """
        friendships = self.get_queryset()
        serializer = self.get_serializer(friendships, many=True)

        return Response({
            'friendships': serializer.data,
            'count': len(friendships)
        })

    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        """
        Get pending friendship requests for the current user.

        Returns friendship requests that the user has received and are pending.
        """
        pending_friendships = Friendship.objects.filter(
            to_user=request.user,
            status='pending'
        ).select_related('from_user')

        serializer = FriendshipListSerializer(pending_friendships, many=True)

        return Response({
            'pending_requests': serializer.data,
            'count': len(pending_friendships)
        })

    @action(detail=False, methods=['get'])
    def sent_requests(self, request):
        """
        Get friendship requests sent by the current user.

        Returns friendship requests that the user has sent and are pending.
        """
        sent_friendships = Friendship.objects.filter(
            from_user=request.user,
            status='pending'
        ).select_related('to_user')

        serializer = FriendshipListSerializer(sent_friendships, many=True)

        return Response({
            'sent_requests': serializer.data,
            'count': len(sent_friendships)
        })

    @action(detail=False, methods=['get'])
    def friends(self, request):
        """
        Get current user's friends list.

        Returns accepted friends, followers, and following lists.
        """
        user = request.user

        # Get friends, followers, and following
        friends = Friendship.get_friends(user)
        followers = Friendship.get_followers(user)
        following = Friendship.get_following(user)

        # Serialize the data
        friends_serializer = UserListSerializer(friends, many=True)
        followers_serializer = UserListSerializer(followers, many=True)
        following_serializer = UserListSerializer(following, many=True)

        return Response({
            'friends': friends_serializer.data,
            'followers': followers_serializer.data,
            'following': following_serializer.data,
            'friends_count': len(friends),
            'followers_count': len(followers),
            'following_count': len(following)
        })

    @action(detail=False, methods=['get'])
    def nearby_friends(self, request):
        """
        Find nearby friends based on geographic coordinates.

        Returns friends within a specified radius (default 10km) of the requesting user.
        """
        user = request.user
        radius = float(request.query_params.get('radius', 10))  # Default 10km

        if not user.has_location:
            return Response(
                {'error': 'User location not available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's friends
        friends = Friendship.get_friends(user)

        # Filter friends with location data
        friends_with_location = friends.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )

        nearby_friends = []
        user_location = user.get_location_tuple()

        for friend in friends_with_location:
            friend_location = friend.get_location_tuple()
            if friend_location:
                distance = geodesic(user_location, friend_location).kilometers
                if distance <= radius:
                    friend_data = UserListSerializer(friend, context={'request': request}).data
                    friend_data['distance_km'] = round(distance, 2)
                    nearby_friends.append(friend_data)

        # Sort by distance
        nearby_friends.sort(key=lambda x: x['distance_km'])

        logger.info(
            f"Nearby friends query for user {user.email}: "
            f"{len(nearby_friends)} found within {radius}km"
        )

        return Response({
            'user_location': user_location,
            'radius_km': radius,
            'nearby_friends': nearby_friends,
            'count': len(nearby_friends)
        })

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get friendship status with a specific user.

        Returns the friendship status between the current user and a specified user.
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if friendship exists
        friendship = Friendship.objects.filter(
            Q(from_user=request.user, to_user=target_user) |
            Q(from_user=target_user, to_user=request.user)
        ).first()

        are_friends = Friendship.are_friends(request.user, target_user)
        friendship_status = friendship.status if friendship else None
        friendship_id = str(friendship.id) if friendship else None

        # Determine if user can send a request
        can_send_request = not friendship or friendship.status in ['declined', 'blocked']

        return Response({
            'are_friends': are_friends,
            'friendship_status': friendship_status,
            'friendship_id': friendship_id,
            'can_send_request': can_send_request
        })

    @action(detail=True, methods=['post'])
    def perform_action(self, request, pk=None):
        """
        Perform actions on a friendship (accept, decline, block, unblock).

        Allows users to perform various actions on friendship relationships.
        """
        try:
            friendship = self.get_object()
        except Friendship.DoesNotExist:
            return Response(
                {'error': 'Friendship not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has permission to perform actions on this friendship
        if friendship.from_user != request.user and friendship.to_user != request.user:
            return Response(
                {'error': 'You do not have permission to perform actions on this friendship'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            data=request.data,
            context={'friendship': friendship}
        )

        if serializer.is_valid():
            action = serializer.validated_data['action']

            # Perform the action
            if action == 'accept':
                friendship.accept()
            elif action == 'decline':
                friendship.decline()
            elif action == 'block':
                friendship.block()
            elif action == 'unblock':
                friendship.unblock()

            logger.info(
                f"Friendship action performed: {action} by {request.user.email} "
                f"on friendship {friendship.id}"
            )

            return Response({
                'message': f'Friendship {action}ed successfully',
                'friendship': FriendshipSerializer(friendship).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search_friends(self, request):
        """
        Search through user's friends by name.

        Returns friends whose names match the search query.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user's friends
        friends = Friendship.get_friends(request.user)

        # Filter friends by search query
        matching_friends = friends.filter(
            Q(name__icontains=query) | Q(email__icontains=query)
        )

        serializer = UserListSerializer(matching_friends, many=True, context={'request': request})

        logger.info(
            f"Friend search by {request.user.email}: query='{query}', results={len(matching_friends)}"
        )

        return Response({
            'query': query,
            'results': serializer.data,
            'count': len(matching_friends)
        })
