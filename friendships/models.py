"""
Friendship model for managing user relationships.

This module defines the Friendship model to handle user relationships
including following/followers functionality.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Friendship(models.Model):
    """
    Friendship model to manage user relationships.

    This model handles the relationship between users including:
    - Following/followers relationships
    - Friendship status (pending, accepted, blocked)
    - Timestamps for relationship events
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('blocked', 'Blocked'),
        ('declined', 'Declined'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship participants
    from_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='friendships_initiated',
        verbose_name="From User"
    )
    to_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='friendships_received',
        verbose_name="To User"
    )

    # Relationship status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Accepted At")

    class Meta:
        """Meta options for the Friendship model."""
        verbose_name = "Friendship"
        verbose_name_plural = "Friendships"
        db_table = 'friendships'
        unique_together = ['from_user', 'to_user']
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """String representation of the Friendship model."""
        return f"{self.from_user.name} -> {self.to_user.name} ({self.status})"

    def clean(self):
        """Validate friendship data."""
        if self.from_user == self.to_user:
            raise ValidationError("Users cannot be friends with themselves.")

        # Check for existing friendship in either direction
        existing_friendship = Friendship.objects.filter(
            models.Q(from_user=self.from_user, to_user=self.to_user) |
            models.Q(from_user=self.to_user, to_user=self.from_user)
        ).exclude(id=self.id)

        if existing_friendship.exists():
            raise ValidationError("A friendship relationship already exists between these users.")

    def save(self, *args, **kwargs):
        """Save the friendship and handle status changes."""
        self.clean()

        # Set accepted_at timestamp when status changes to accepted
        if self.status == 'accepted' and not self.accepted_at:
            self.accepted_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_accepted(self):
        """Check if the friendship is accepted."""
        return self.status == 'accepted'

    @property
    def is_pending(self):
        """Check if the friendship is pending."""
        return self.status == 'pending'

    @property
    def is_blocked(self):
        """Check if the friendship is blocked."""
        return self.status == 'blocked'

    def accept(self):
        """Accept the friendship request."""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()

    def decline(self):
        """Decline the friendship request."""
        self.status = 'declined'
        self.save()

    def block(self):
        """Block the friendship."""
        self.status = 'blocked'
        self.save()

    def unblock(self):
        """Unblock the friendship."""
        self.status = 'pending'
        self.save()

    @classmethod
    def get_friends(cls, user):
        """
        Get all accepted friends for a user.

        Args:
            user: User instance

        Returns:
            QuerySet: Friends of the user
        """
        from users.models import User

        friend_ids = cls.objects.filter(
            models.Q(from_user=user, status='accepted') |
            models.Q(to_user=user, status='accepted')
        ).values_list('from_user_id', 'to_user_id')

        # Extract friend IDs (excluding the user themselves)
        friend_ids = set()
        for from_id, to_id in friend_ids:
            if from_id == user.id:
                friend_ids.add(to_id)
            else:
                friend_ids.add(from_id)

        return User.objects.filter(id__in=friend_ids)

    @classmethod
    def get_followers(cls, user):
        """
        Get all followers for a user.

        Args:
            user: User instance

        Returns:
            QuerySet: Followers of the user
        """
        from users.models import User

        follower_ids = cls.objects.filter(
            to_user=user,
            status='accepted'
        ).values_list('from_user_id', flat=True)

        return User.objects.filter(id__in=follower_ids)

    @classmethod
    def get_following(cls, user):
        """
        Get all users that a user is following.

        Args:
            user: User instance

        Returns:
            QuerySet: Users that the user is following
        """
        from users.models import User

        following_ids = cls.objects.filter(
            from_user=user,
            status='accepted'
        ).values_list('to_user_id', flat=True)

        return User.objects.filter(id__in=following_ids)

    @classmethod
    def are_friends(cls, user1, user2):
        """
        Check if two users are friends.

        Args:
            user1: First user instance
            user2: Second user instance

        Returns:
            bool: True if users are friends, False otherwise
        """
        return cls.objects.filter(
            models.Q(from_user=user1, to_user=user2, status='accepted') |
            models.Q(from_user=user2, to_user=user1, status='accepted')
        ).exists()
