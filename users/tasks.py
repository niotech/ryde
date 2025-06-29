"""
Background tasks for the User app.

This module contains Celery tasks for user-related background processing.
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import User

logger = logging.getLogger(__name__)


@shared_task
def cleanup_inactive_users():
    """
    Clean up users who haven't logged in for a long time.

    This task removes users who haven't been active for more than 1 year.
    """
    cutoff_date = timezone.now() - timedelta(days=365)
    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date,
        is_active=True
    )

    count = inactive_users.count()
    inactive_users.update(is_active=False)

    logger.info(f"Deactivated {count} inactive users")
    return count


@shared_task
def send_welcome_email(user_id):
    """
    Send welcome email to new users.

    Args:
        user_id: ID of the user to send welcome email to
    """
    try:
        user = User.objects.get(id=user_id)
        # Here you would integrate with your email service
        # For example, using Django's email backend or a service like SendGrid

        logger.info(f"Welcome email sent to {user.email}")
        return True
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False


@shared_task
def update_user_statistics():
    """
    Update user statistics for analytics.

    This task calculates and stores various user statistics.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    users_with_location = User.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).count()

    # Here you would store these statistics in a cache or database
    # For example, using Django's cache framework

    logger.info(f"Updated user statistics: Total={total_users}, "
                f"Active={active_users}, WithLocation={users_with_location}")

    return {
        'total_users': total_users,
        'active_users': active_users,
        'users_with_location': users_with_location
    }


@shared_task
def process_user_location_update(user_id, latitude, longitude):
    """
    Process user location updates in the background.

    Args:
        user_id: ID of the user
        latitude: New latitude
        longitude: New longitude
    """
    try:
        user = User.objects.get(id=user_id)
        user.latitude = latitude
        user.longitude = longitude
        user.save()

        logger.info(f"Updated location for user {user.email}: "
                   f"({latitude}, {longitude})")
        return True
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False


@shared_task
def notify_nearby_friends(user_id, radius=10):
    """
    Notify friends when a user updates their location.

    Args:
        user_id: ID of the user who updated their location
        radius: Radius in kilometers to check for nearby friends
    """
    try:
        user = User.objects.get(id=user_id)

        if not user.has_location:
            logger.warning(f"User {user.email} has no location data")
            return False

        # Here you would implement the logic to notify nearby friends
        # This could involve sending push notifications, emails, etc.

        logger.info(f"Notified nearby friends for user {user.email}")
        return True
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False