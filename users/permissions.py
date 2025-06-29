"""
Custom permissions for the User API.

This module defines custom permission classes for controlling
access to user-related resources.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.

    This permission allows read access to any authenticated user,
    but only allows write access to the owner of the object.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the object.

        Args:
            request: The request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admin users to access an object.

    This permission allows access only to the owner of the object or
    users with admin privileges.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the object.

        Args:
            request: The request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Admin users have full access
        if request.user.is_staff:
            return True

        # Owners have full access
        return obj == request.user


class IsAuthenticatedOrCreate(permissions.BasePermission):
    """
    Custom permission to allow unauthenticated users to create objects.

    This permission allows unauthenticated users to create new objects
    (e.g., user registration) but requires authentication for other operations.
    """

    def has_permission(self, request, view):
        """
        Check if the user has permission to perform the action.

        Args:
            request: The request object
            view: The view being accessed

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Allow unauthenticated users to create objects
        if request.method == 'POST':
            return True

        # Require authentication for other methods
        return request.user and request.user.is_authenticated