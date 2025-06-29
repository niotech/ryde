"""
Serializers for the Friendship model.

This module provides serializers for handling friendship relationships
in REST API requests and responses.
"""

from django.db import models
from rest_framework import serializers
from .models import Friendship
from users.serializers import UserListSerializer


class FriendshipSerializer(serializers.ModelSerializer):
    """
    Serializer for Friendship model with all fields.

    This serializer handles complete friendship data including
    user information and relationship status.
    """

    from_user = UserListSerializer(read_only=True)
    to_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = [
            'id', 'from_user', 'to_user', 'status',
            'created_at', 'updated_at', 'accepted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'accepted_at']


class FriendshipCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new friendships.

    This serializer handles friendship request creation with validation.
    """

    class Meta:
        model = Friendship
        fields = ['to_user']

    def validate_to_user(self, value):
        """Validate the target user for friendship request."""
        request_user = self.context['request'].user

        # Cannot send friend request to yourself
        if value == request_user:
            raise serializers.ValidationError("You cannot send a friend request to yourself.")

        # Check if friendship already exists
        existing_friendship = Friendship.objects.filter(
            models.Q(from_user=request_user, to_user=value) |
            models.Q(from_user=value, to_user=request_user)
        )

        if existing_friendship.exists():
            raise serializers.ValidationError("A friendship relationship already exists with this user.")

        return value

    def create(self, validated_data):
        """Create a new friendship request."""
        validated_data['from_user'] = self.context['request'].user
        return super().create(validated_data)


class FriendshipUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating friendship status.

    This serializer handles friendship status updates (accept, decline, block).
    """

    class Meta:
        model = Friendship
        fields = ['status']

    def validate_status(self, value):
        """Validate status changes."""
        friendship = self.instance
        current_status = friendship.status

        # Only allow certain status transitions
        allowed_transitions = {
            'pending': ['accepted', 'declined', 'blocked'],
            'accepted': ['blocked'],
            'blocked': ['pending'],  # unblock
            'declined': ['pending'],  # resend request
        }

        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'."
            )

        return value


class FriendshipListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing friendships with minimal information.

    This serializer is used for friendship lists to reduce payload size.
    """

    from_user = UserListSerializer(read_only=True)
    to_user = UserListSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at']


class FriendshipStatusSerializer(serializers.Serializer):
    """
    Serializer for friendship status information.

    This serializer provides information about the friendship status
    between two users.
    """

    are_friends = serializers.BooleanField()
    friendship_status = serializers.CharField(allow_null=True)
    friendship_id = serializers.UUIDField(allow_null=True)
    can_send_request = serializers.BooleanField()


class UserFriendsSerializer(serializers.Serializer):
    """
    Serializer for user's friends list.

    This serializer provides information about a user's friends,
    followers, and following lists.
    """

    friends = UserListSerializer(many=True)
    followers = UserListSerializer(many=True)
    following = UserListSerializer(many=True)
    friends_count = serializers.IntegerField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()


class NearbyFriendsSerializer(serializers.Serializer):
    """
    Serializer for nearby friends with distance information.

    This serializer provides information about friends within a
    specified radius with distance calculations.
    """

    user_location = serializers.ListField(child=serializers.FloatField())
    radius_km = serializers.FloatField()
    nearby_friends = serializers.ListField()
    count = serializers.IntegerField()


class FriendshipActionSerializer(serializers.Serializer):
    """
    Serializer for friendship actions.

    This serializer handles friendship actions like accept, decline, block.
    """

    action = serializers.ChoiceField(choices=['accept', 'decline', 'block', 'unblock'])

    def validate_action(self, value):
        """Validate the action based on current friendship status."""
        friendship = self.context.get('friendship')
        if not friendship:
            raise serializers.ValidationError("Friendship not found.")

        current_status = friendship.status
        allowed_actions = {
            'pending': ['accept', 'decline', 'block'],
            'accepted': ['block'],
            'blocked': ['unblock'],
            'declined': [],  # No actions allowed on declined friendships
        }

        if value not in allowed_actions.get(current_status, []):
            raise serializers.ValidationError(
                f"Action '{value}' is not allowed for friendship status '{current_status}'."
            )

        return value