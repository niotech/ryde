"""
Serializers for the User model.

This module provides serializers for handling User model data
in REST API requests and responses.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with all fields.

    This serializer handles the complete user data including
    geographic coordinates and computed fields.
    """

    age = serializers.ReadOnlyField(help_text="Calculated age based on date of birth")
    has_location = serializers.ReadOnlyField(help_text="Whether user has geographic coordinates")

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'dob', 'address', 'description',
            'latitude', 'longitude', 'created_at', 'updated_at',
            'age', 'has_location'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'age', 'has_location']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'name': {'required': True},
        }

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate geographic coordinates consistency."""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')

        # If one coordinate is provided, both must be provided
        if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.

    This serializer includes password validation and user creation logic.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'name', 'password', 'password_confirm',
            'dob', 'address', 'description', 'latitude', 'longitude'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
        }

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate password confirmation and geographic coordinates."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")

        # Validate geographic coordinates consistency
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')

        if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = validated_data['email']
        user = User.objects.create_user(username=email, **validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing users.

    This serializer allows partial updates and excludes sensitive fields.
    """

    class Meta:
        model = User
        fields = [
            'name', 'dob', 'address', 'description',
            'latitude', 'longitude'
        ]

    def validate(self, attrs):
        """Validate geographic coordinates consistency."""
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')

        # If one coordinate is provided, both must be provided
        if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )

        return attrs


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    This serializer handles authentication using email and password.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled."
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                "Must include 'email' and 'password'."
            )

        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.

    This serializer handles password change with current password validation.
    """

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate new password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

    def save(self):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users with minimal information.

    This serializer is used for user lists to reduce payload size.
    """

    age = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'age', 'has_location', 'created_at']
        read_only_fields = ['id', 'age', 'has_location', 'created_at']