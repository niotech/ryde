"""
URL patterns for the Friendship API.

This module defines the URL routing for friendship-related endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FriendshipViewSet

# Create router for FriendshipViewSet
router = DefaultRouter()
router.register(r'friendships', FriendshipViewSet, basename='friendship')

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
]