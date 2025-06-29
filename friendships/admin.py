"""
Admin configuration for the Friendship model.

This module provides Django admin interface configuration for friendship management.
"""

from django.contrib import admin
from .models import Friendship


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Friendship model.

    Provides a comprehensive admin interface for friendship management
    with custom display fields and filtering options.
    """

    list_display = [
        'id', 'from_user', 'to_user', 'status', 'created_at',
        'accepted_at', 'get_duration'
    ]
    list_filter = ['status', 'created_at', 'accepted_at']
    search_fields = [
        'from_user__name', 'from_user__email',
        'to_user__name', 'to_user__email'
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Relationship', {
            'fields': ('from_user', 'to_user', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )

    def get_duration(self, obj):
        """Display friendship duration in admin list."""
        if obj.accepted_at:
            duration = obj.accepted_at - obj.created_at
            return f"{duration.days} days"
        return "Not accepted"
    get_duration.short_description = 'Duration'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('from_user', 'to_user')
