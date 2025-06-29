"""
Views for the User API.

This module provides REST API views for user management including
CRUD operations, authentication, and location-based features.
"""

import logging
from django.contrib.auth import login, logout
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authtoken.models import Token
from geopy.distance import geodesic

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserLoginSerializer, PasswordChangeSerializer, UserListSerializer
)
from .permissions import IsOwnerOrReadOnly

logger = logging.getLogger(__name__)


class UserViewSet(ModelViewSet):
    """
    ViewSet for User model providing CRUD operations.

    This ViewSet handles all user-related operations including:
    - User registration and authentication
    - Profile management
    - Location-based queries
    - Password management
    """

    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'email']
    search_fields = ['name', 'email', 'address', 'description']
    ordering_fields = ['name', 'email', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        return UserSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ['create', 'login']:
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy', 'change_password']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Return filtered queryset based on user permissions."""
        # Handle schema generation for Swagger/OpenAPI
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()

        if self.action == 'list' and not self.request.user.is_staff:
            # Non-staff users can only see basic user information
            return User.objects.filter(is_active=True)
        return User.objects.all()

    def perform_create(self, serializer):
        """Create user and log the action."""
        user = serializer.save()
        logger.info(f"New user created: {user.email}")

        # Create authentication token for the new user
        Token.objects.create(user=user)

    def perform_update(self, serializer):
        """Update user and log the action."""
        user = serializer.save()
        logger.info(f"User updated: {user.email}")

    def perform_destroy(self, instance):
        """Delete user and log the action."""
        logger.info(f"User deleted: {instance.email}")
        instance.delete()

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        User login endpoint.

        Authenticates user with email and password, returns authentication token.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)

            # Get or create token
            token, created = Token.objects.get_or_create(user=user)

            logger.info(f"User logged in: {user.email}")

            return Response({
                'token': token.key,
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        User logout endpoint.

        Logs out the current user and invalidates the session.
        """
        logger.info(f"User logged out: {request.user.email}")
        logout(request)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change password endpoint.

        Allows authenticated users to change their password.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Password changed for user: {request.user.email}")
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user profile.

        Returns the profile of the currently authenticated user.
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
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

        # Get all users with location data
        users_with_location = User.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True
        ).exclude(id=user.id)

        nearby_users = []
        user_location = user.get_location_tuple()

        for other_user in users_with_location:
            other_location = other_user.get_location_tuple()
            if other_location:
                distance = geodesic(user_location, other_location).kilometers
                if distance <= radius:
                    user_data = UserListSerializer(other_user, context={'request': request}).data
                    user_data['distance_km'] = round(distance, 2)
                    nearby_users.append(user_data)

        # Sort by distance
        nearby_users.sort(key=lambda x: x['distance_km'])

        logger.info(f"Nearby friends query for user {user.email}: {len(nearby_users)} found within {radius}km")

        return Response({
            'user_location': user_location,
            'radius_km': radius,
            'nearby_users': nearby_users,
            'count': len(nearby_users)
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search_by_name(self, request):
        """
        Search users by name.

        Returns users whose names match the search query.
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        users = User.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query),
            is_active=True
        ).exclude(id=request.user.id)

        serializer = UserListSerializer(users, many=True, context={'request': request})

        logger.info(f"User search by {request.user.email}: query='{query}', results={len(users)}")

        return Response({
            'query': query,
            'results': serializer.data,
            'count': len(users)
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request, pk=None):
        """
        Get user profile by ID.

        Returns detailed profile information for a specific user.
        """
        try:
            user = self.get_object()
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
