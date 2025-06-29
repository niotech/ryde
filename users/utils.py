"""
Utility functions for the User API.

This module provides utility functions and helpers for the user management system.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error responses.

    This function provides consistent error response formatting
    and logs exceptions for debugging purposes.

    Args:
        exc: The exception that was raised
        context: The context in which the exception occurred

    Returns:
        Response: Formatted error response
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the exception
        logger.error(f"API Exception: {exc} in {context['view'].__class__.__name__}")

        # Customize the error response format
        error_data = {
            'error': True,
            'message': response.data.get('detail', str(exc)),
            'status_code': response.status_code,
        }

        # Add field-specific errors if available
        if isinstance(response.data, dict) and 'detail' not in response.data:
            error_data['fields'] = response.data

        response.data = error_data

    return response


def validate_coordinates(latitude, longitude):
    """
    Validate geographic coordinates.

    Args:
        latitude: Latitude value
        longitude: Longitude value

    Returns:
        tuple: (is_valid, error_message)
    """
    if latitude is None or longitude is None:
        return False, "Both latitude and longitude must be provided"

    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return False, "Latitude and longitude must be valid numbers"

    if not (-90 <= lat <= 90):
        return False, "Latitude must be between -90 and 90 degrees"

    if not (-180 <= lon <= 180):
        return False, "Longitude must be between -180 and 180 degrees"

    return True, None


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two geographic points using Haversine formula.

    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point

    Returns:
        float: Distance in kilometers
    """
    from math import radians, cos, sin, asin, sqrt

    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def format_user_data(user, include_sensitive=False):
    """
    Format user data for API responses.

    Args:
        user: User instance
        include_sensitive: Whether to include sensitive information

    Returns:
        dict: Formatted user data
    """
    data = {
        'id': str(user.id),
        'name': user.name,
        'email': user.email,
        'created_at': user.created_at.isoformat(),
        'has_location': user.has_location,
    }

    if include_sensitive:
        data.update({
            'dob': user.dob.isoformat() if user.dob else None,
            'address': user.address,
            'description': user.description,
            'latitude': float(user.latitude) if user.latitude else None,
            'longitude': float(user.longitude) if user.longitude else None,
            'updated_at': user.updated_at.isoformat(),
        })

    return data