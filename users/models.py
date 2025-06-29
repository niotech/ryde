"""
User model for the Ryde application.

This module defines the User model with all required fields including
geographic coordinates for location-based features.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.

    This manager handles user creation using email instead of username.
    """

    def create_user(self, username, email=None, name=None, password=None, **extra_fields):
        # For compatibility with Django's internal calls, username is the first argument
        # but we use it as email since our model uses email as the unique identifier
        if email is None:
            email = username

        if not email:
            raise ValueError('The Email field must be set')

        if not name:
            raise ValueError('The Name field must be set')

        # Validate coordinates if provided
        latitude = extra_fields.get('latitude')
        longitude = extra_fields.get('longitude')

        if latitude is not None:
            if not (-90 <= float(latitude) <= 90):
                raise ValueError("Latitude must be between -90 and 90")

        if longitude is not None:
            if not (-180 <= float(longitude) <= 180):
                raise ValueError("Longitude must be between -180 and 180")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, name=None, password=None, **extra_fields):
        # For compatibility with Django's internal calls, username is the first argument
        # but we use it as email since our model uses email as the unique identifier
        if email is None:
            email = username

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username=email, email=email, name=name, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model extending Django's AbstractUser.

    This model includes all the required fields for the Ryde application:
    - Basic user information (name, date of birth, address, description)
    - Geographic coordinates for location-based features
    - Timestamps for creation and updates
    - UUID as primary key for better security
    """

    # Override the default id field with UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Override username to be email
    email = models.EmailField(unique=True, verbose_name="Email Address")

    # Required fields from the specification
    name = models.CharField(max_length=255, verbose_name="Full Name")
    dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
    address = models.TextField(verbose_name="Address", blank=True)
    description = models.TextField(verbose_name="Description", blank=True)

    # Geographic coordinates for location-based features
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90, "Latitude must be between -90 and 90"),
            MaxValueValidator(90, "Latitude must be between -90 and 90")
        ],
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180, "Longitude must be between -180 and 180"),
            MaxValueValidator(180, "Longitude must be between -180 and 180")
        ],
        verbose_name="Longitude"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    # Fix reverse accessor clashes by adding related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    # Use custom manager
    objects = UserManager()

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        """Meta options for the User model."""
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        """String representation of the User model."""
        return f"{self.name} ({self.email})"

    @property
    def age(self):
        """Calculate user's age based on date of birth."""
        if self.dob:
            today = timezone.now().date()
            return today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )
        return None

    @property
    def has_location(self):
        """Check if user has geographic coordinates."""
        return self.latitude is not None and self.longitude is not None

    def get_location_tuple(self):
        """Get location as a tuple of (latitude, longitude)."""
        if self.has_location:
            return (float(self.latitude), float(self.longitude))
        return None
