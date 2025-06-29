"""
Admin configuration for the User model.

This module provides Django admin interface configuration for user management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the User model.

    Provides a comprehensive admin interface for user management
    with custom display fields and filtering options.
    """

    model = User
    list_display = ('email', 'name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('email', 'name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password')}),
        ('Personal info', {'fields': ('dob', 'address', 'description', 'latitude', 'longitude')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    readonly_fields = ('created_at', 'updated_at')

    def get_location_display(self, obj):
        """Display location information in admin list."""
        if obj.has_location:
            return format_html(
                '<span style="color: green;">✓</span> '
                '({:.4f}, {:.4f})',
                obj.latitude, obj.longitude
            )
        return format_html('<span style="color: red;">✗</span>')
    get_location_display.short_description = 'Location'

    def age(self, obj):
        """Display user age in admin list."""
        return obj.age or 'N/A'
    age.short_description = 'Age'

    def has_location(self, obj):
        """Display location availability in admin list."""
        return obj.has_location
    has_location.boolean = True
    has_location.short_description = 'Has Location'
