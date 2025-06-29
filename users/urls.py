"""
URL patterns for the User API.

This module defines the URL routing for user-related endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router for UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
]